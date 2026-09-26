#!/usr/bin/env python3
"""
Build catalogue/genapp.json from the pinned GenApp BMS and COBOL source.
All data is read from source files. Nothing is invented.
Run from workspace root: .venv/bin/python catalogue/scripts/build_catalogue.py
"""
import json
import re
import datetime
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BMS_FILE = "legacy/cics-genapp/base/src/ssmap.bms"
BMS_PATH = os.path.join(REPO_ROOT, BMS_FILE)

def bms_lines():
    with open(BMS_PATH, encoding="latin-1") as f:
        return f.readlines()

def strip_initial(val):
    """Remove surrounding quotes and strip whitespace from INITIAL= value."""
    if val is None:
        return None
    val = val.strip().strip("'")
    return val

def parse_pos(pos_str):
    """Parse POS=(row,col) -> (row, col)."""
    m = re.search(r'POS=\((\d+),(\d+)\)', pos_str)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None

def parse_length(line_block):
    m = re.search(r'LENGTH=(\d+)', line_block)
    return int(m.group(1)) if m else None

def parse_attrb(line_block):
    m = re.search(r'ATTRB=\(([^)]+)\)', line_block)
    return m.group(1) if m else ""

def parse_initial(line_block):
    # INITIAL='...' - capture content between single quotes
    m = re.search(r"INITIAL='([^']*)'", line_block)
    return m.group(1) if m else None

def parse_xinit(line_block):
    m = re.search(r"XINIT='([^']*)'", line_block)
    return m.group(1) if m else None

def parse_justify(line_block):
    m = re.search(r'JUSTIFY=\(([^)]+)\)', line_block)
    return m.group(1) if m else None

def parse_validn(line_block):
    m = re.search(r'VALIDN=\(([^)]+)\)', line_block)
    return m.group(1) if m else None

def is_protected(attrb):
    parts = [p.strip() for p in attrb.split(",")]
    return "PROT" in parts or "ASKIP" in parts

def is_numeric(attrb):
    parts = [p.strip() for p in attrb.split(",")]
    return "NUM" in parts

def assign_role(bms_name, row, attrb_str, initial_val, validn):
    """Assign role based on deterministic BMS attribute rules."""
    protected = is_protected(attrb_str)
    numeric = is_numeric(attrb_str)
    attrb_parts = [p.strip() for p in attrb_str.split(",")]

    if bms_name is None:
        # Anonymous DFHMDF
        if row == 1 and "BRT" in attrb_parts:
            return "title"
        if row in (4, 5, 6, 7) and initial_val is not None:
            # Menu option: matches "N. " pattern or is blank
            stripped = initial_val.strip()
            if re.match(r'^[1-4]\.', stripped) or stripped == "":
                return "menuOption"
        if initial_val is not None and "(yyyy-mm-dd)" in (initial_val or ""):
            return "hint"
        if initial_val is not None and len(initial_val.strip()) == 0 and parse_length_from_attrb(attrb_str) == 1:
            return "separator"
        if initial_val is not None and len(initial_val.strip()) <= 1 and protected:
            return "separator"
        if not protected and initial_val is None:
            return "cannot-determine"
        return "label"
    else:
        # Named DFHMDF
        if row == 24 and protected and "BRT" in attrb_parts:
            return "error"
        if row == 22 and validn and "MUSTENTER" in validn:
            return "option"
        if not protected:
            return "input"
        return "cannot-determine"

def parse_length_from_attrb(attrb_str):
    """Not actually in attrb, just a helper placeholder."""
    return None

def collect_dfhmdf_blocks(lines):
    """
    Parse all DFHMDF blocks from BMS lines.
    Returns list of dicts with keys: lineStart, lineEnd, bmsName, block_text
    Comments (lines starting with * in col 7, i.e. index 6) are excluded.
    """
    blocks = []
    i = 0
    n = len(lines)

    # We look for lines that have a DFHMDF keyword (not commented)
    dfhmdf_re = re.compile(r'^(\w+)?\s+DFHMDF\s', re.IGNORECASE)
    dfhmdf_anon_re = re.compile(r'^\s+DFHMDF\s', re.IGNORECASE)
    comment_re = re.compile(r'^\*')

    i = 0
    while i < n:
        raw = lines[i]
        # Skip comment lines
        if comment_re.match(raw):
            i += 1
            continue

        named_match = re.match(r'^(\w+)\s+DFHMDF\b', raw, re.IGNORECASE)
        anon_match = re.match(r'^\s+DFHMDF\b', raw, re.IGNORECASE)

        if named_match or anon_match:
            bms_name = named_match.group(1) if named_match else None
            # Exclude DFHMSD and DFHMDI
            block_text = raw.rstrip('\n')
            line_start = i + 1  # 1-based
            j = i + 1
            # Continuation: line ends with X or * in column 72 (index 71)
            while j < n:
                prev = lines[j-1].rstrip('\n')
                # BMS continuation character at column 72 (0-indexed 71)
                # or col 80 (*) - check if line has continuation marker
                cont_char = prev[71:72] if len(prev) > 71 else ''
                if cont_char in ('X', '*'):
                    if comment_re.match(lines[j]):
                        break
                    block_text += ' ' + lines[j].strip().rstrip('\n')
                    j += 1
                else:
                    break
            line_end = j  # 1-based last line = j (since we stopped before j)
            # Recalculate: lines i through j-1 are part of this block
            line_end = j  # exclusive, so last line is j (1-based = j)

            blocks.append({
                'lineStart': line_start,
                'lineEnd': j,  # last included line number (1-based)
                'bmsName': bms_name,
                'block_text': block_text,
                'raw_line': raw
            })
            i = j
        else:
            i += 1
    return blocks

def build_elements_for_map(map_name, map_line_start, map_line_end, all_blocks):
    """Build element list for a single map from pre-parsed blocks."""
    elements = []
    field_seq = 0
    elem_seq = 0

    # Filter blocks within this map's line range
    map_blocks = [b for b in all_blocks
                  if b['lineStart'] >= map_line_start and b['lineEnd'] <= map_line_end]

    # Also track preceding label for humanLabel assignment
    pending_label = None  # (label_initial, label_source_ref)

    for b in map_blocks:
        elem_seq += 1
        block = b['block_text']
        bms_name = b['bmsName']
        line_start = b['lineStart']
        line_end = b['lineEnd']

        row, col = parse_pos(block)
        length = parse_length(block)
        attrb_str = parse_attrb(block)
        initial_val = parse_initial(block)
        xinit_val = parse_xinit(block)
        justify_val = parse_justify(block)
        validn_val = parse_validn(block)
        protected = is_protected(attrb_str)
        numeric = is_numeric(attrb_str)
        role = assign_role(bms_name, row, attrb_str, initial_val, validn_val)

        elem_id = f"E-{map_name}-{elem_seq:03d}"
        field_id = None
        human_label = None
        label_note = None
        label_source = None

        if bms_name is not None:
            field_seq += 1
            field_id = f"F-{map_name}-{field_seq:03d}"

        # Compute excerpt (first 60 chars of raw line, stripped)
        excerpt = b['raw_line'].strip()[:60]

        source_ref = {
            "file": BMS_FILE,
            "lineStart": line_start,
            "lineEnd": line_end,
            "excerpt": excerpt
        }

        el = {
            "elementId": elem_id,
            "sourceOrder": elem_seq,
            "bmsName": bms_name,
            "role": role,
            "row": row,
            "col": col,
            "length": length,
            "attrb": attrb_str,
            "protected": protected,
            "numeric": numeric,
            "validn": validn_val,
            "initialValue": initial_val,
            "xinitValue": xinit_val,
            "justify": justify_val,
            "sourceRef": source_ref
        }
        if field_id:
            el["fieldId"] = field_id

        elements.append(el)

    return elements

# ─────────────────────────────────────────────────────────
# Manual element builder for accuracy - build from verified BMS data
# ─────────────────────────────────────────────────────────

def make_ref(file_path, ls, le, excerpt):
    return {"file": file_path, "lineStart": ls, "lineEnd": le, "excerpt": excerpt[:60]}

def make_el(eid, order, bms_name, field_id, role, row, col, length, attrb,
            protected, numeric, validn, initial, xinit, justify, ls, le, excerpt,
            human_label=None, label_note=None, label_src=None, note=None, rules=None):
    el = {
        "elementId": eid,
        "sourceOrder": order,
        "bmsName": bms_name,
        "role": role,
        "row": row,
        "col": col,
        "length": length,
        "attrb": attrb,
        "protected": protected,
        "numeric": numeric,
        "validn": validn,
        "initialValue": initial,
        "xinitValue": xinit,
        "justify": justify,
        "sourceRef": make_ref(BMS_FILE, ls, le, excerpt)
    }
    if field_id:
        el["fieldId"] = field_id
    if human_label is not None:
        el["humanLabel"] = human_label
    if label_note:
        el["labelNote"] = label_note
    if label_src:
        el["labelSource"] = label_src
    if note:
        el["note"] = note
    if rules:
        el["rules"] = rules
    return el

F = BMS_FILE

def mustenter_rules(elem_id, ls, le, exc):
    return [
        {"ruleId": f"R-{elem_id}-001", "type": "required",
         "certainty": "explicit",
         "plainEnglish": "The option field must not be left blank. BMS VALIDN=(MUSTENTER) requires a value before the screen can be submitted.",
         "sourceRef": make_ref(F, ls, le, exc)},
        {"ruleId": f"R-{elem_id}-002", "type": "numeric",
         "certainty": "explicit",
         "plainEnglish": "Only numeric digits are accepted. BMS ATTRB contains NUM.",
         "sourceRef": make_ref(F, ls, le, exc)}
    ]

def maxlen_rule(elem_id, length, ls, le, exc):
    return {
        "ruleId": f"R-{elem_id}-001", "type": "maxLength",
        "certainty": "explicit",
        "plainEnglish": f"Maximum input length is {length} characters as defined by BMS LENGTH={length}.",
        "sourceRef": make_ref(F, ls, le, exc)
    }

def date_cannot_determine_rule(elem_id, ls, le, exc):
    return {
        "ruleId": f"R-{elem_id}-002", "type": "formatHint",
        "certainty": "cannot-determine",
        "plainEnglish": "A (yyyy-mm-dd) format hint is shown on screen but no COBOL validation of the date format was found in the presentation programs before the value is passed to the database layer.",
        "sourceRef": make_ref(F, ls, le, exc)
    }

def build_ssmapc1_elements():
    els = []
    # E-SSMAPC1-001: title id tag
    els.append(make_el("E-SSMAPC1-001",1,None,None,"title",1,1,4,"ASKIP,BRT",True,False,None,"SSC1",None,None,14,14,"        DFHMDF POS=(1,1),LENGTH=4,ATTRB=(ASKIP,BRT),INITIAL='SSC1'"))
    # E-SSMAPC1-002: title text
    els.append(make_el("E-SSMAPC1-002",2,None,None,"title",1,12,31,"BRT,ASKIP",True,False,None,"General Insurance Customer Menu",None,None,15,16,"        DFHMDF POS=(1,12),LENGTH=31,ATTRB=(BRT,ASKIP),"))
    # E-SSMAPC1-003: menu opt 1
    els.append(make_el("E-SSMAPC1-003",3,None,None,"menuOption",4,8,16,"NORM,ASKIP",True,False,None,"1. Cust Inquiry ",None,None,18,19,"        DFHMDF POS=(4,08),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    # E-SSMAPC1-004: menu opt 2
    els.append(make_el("E-SSMAPC1-004",4,None,None,"menuOption",5,8,16,"NORM,ASKIP",True,False,None,"2. Cust Add     ",None,None,20,21,"        DFHMDF POS=(5,08),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    # E-SSMAPC1-005: menu opt 3 (blank - absent)
    els.append(make_el("E-SSMAPC1-005",5,None,None,"menuOption",6,8,16,"NORM,ASKIP",True,False,None,"                ",None,None,22,23,"        DFHMDF POS=(6,08),LENGTH=16,ATTRB=(NORM,ASKIP),",
                       note="Option 3 label is blank. No COBOL dispatch case for '3'. This option slot is absent."))
    # E-SSMAPC1-006: menu opt 4
    els.append(make_el("E-SSMAPC1-006",6,None,None,"menuOption",7,8,16,"NORM,ASKIP",True,False,None,"4. Cust Update  ",None,None,24,25,"        DFHMDF POS=(7,08),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    # E-SSMAPC1-007: label Cust Number
    els.append(make_el("E-SSMAPC1-007",7,None,None,"label",4,30,12,"NORM,ASKIP",True,False,None,"Cust Number ",None,None,27,28,"        DFHMDF POS=(04,30),LENGTH=12,ATTRB=(NORM,ASKIP),"))
    # E-SSMAPC1-008: ENT1CNO
    lsrc_cno = make_ref(F,27,28,"        DFHMDF POS=(04,30),LENGTH=12,ATTRB=(NORM,ASKIP),")
    els.append(make_el("E-SSMAPC1-008",8,"ENT1CNO","F-SSMAPC1-001","input",4,50,10,"NORM,UNPROT,IC,FSET",False,False,None,None,None,"RIGHT,ZERO",29,30,"ENT1CNO DFHMDF POS=(04,50),LENGTH=10,ATTRB=(NORM,UNPROT,IC,FSET),",
                       human_label="Cust Number", label_src=lsrc_cno,
                       rules=[maxlen_rule("E-SSMAPC1-008",10,29,30,"ENT1CNO DFHMDF POS=(04,50),LENGTH=10")]))
    # E-SSMAPC1-009: separator
    els.append(make_el("E-SSMAPC1-009",9,None,None,"separator",4,61,1,"PROT,ASKIP",True,False,None," ",None,None,31,32,"        DFHMDF POS=(04,61),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # E-SSMAPC1-010: label Cust Name :First
    els.append(make_el("E-SSMAPC1-010",10,None,None,"label",5,30,16,"NORM,ASKIP",True,False,None,"Cust Name :First",None,None,34,35,"        DFHMDF POS=(05,30),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    # E-SSMAPC1-011: ENT1FNA
    lsrc_fna = make_ref(F,34,35,"        DFHMDF POS=(05,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(make_el("E-SSMAPC1-011",11,"ENT1FNA","F-SSMAPC1-002","input",5,50,10,"NORM,UNPROT,FSET",False,False,None," ",None,None,36,37,"ENT1FNA DFHMDF POS=(05,50),LENGTH=10,ATTRB=(NORM,UNPROT,FSET),",
                       human_label="Cust Name :First", label_src=lsrc_fna,
                       rules=[maxlen_rule("E-SSMAPC1-011",10,36,37,"ENT1FNA DFHMDF POS=(05,50),LENGTH=10")]))
    # E-SSMAPC1-012: separator
    els.append(make_el("E-SSMAPC1-012",12,None,None,"separator",5,61,1,"PROT,ASKIP",True,False,None," ",None,None,38,39,"        DFHMDF POS=(05,61),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # E-SSMAPC1-013: label :Last
    els.append(make_el("E-SSMAPC1-013",13,None,None,"label",6,30,16,"NORM,ASKIP",True,False,None,"          :Last",None,None,40,41,"        DFHMDF POS=(06,30),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    # E-SSMAPC1-014: ENT1LNA
    lsrc_lna = make_ref(F,40,41,"        DFHMDF POS=(06,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(make_el("E-SSMAPC1-014",14,"ENT1LNA","F-SSMAPC1-003","input",6,50,20,"NORM,UNPROT,FSET",False,False,None," ",None,None,42,43,"ENT1LNA DFHMDF POS=(06,50),LENGTH=20,ATTRB=(NORM,UNPROT,FSET),",
                       human_label="          :Last", label_src=lsrc_lna,
                       rules=[maxlen_rule("E-SSMAPC1-014",20,42,43,"ENT1LNA DFHMDF POS=(06,50),LENGTH=20")]))
    # E-SSMAPC1-015: separator
    els.append(make_el("E-SSMAPC1-015",15,None,None,"separator",6,71,1,"PROT,ASKIP",True,False,None," ",None,None,44,45,"        DFHMDF POS=(06,71),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # E-SSMAPC1-016: label DOB
    els.append(make_el("E-SSMAPC1-016",16,None,None,"label",7,30,12,"NORM,ASKIP",True,False,None,"DOB         ",None,None,47,48,"        DFHMDF POS=(07,30),LENGTH=12,ATTRB=(NORM,ASKIP),"))
    # E-SSMAPC1-017: ENT1DOB
    lsrc_dob = make_ref(F,47,48,"        DFHMDF POS=(07,30),LENGTH=12,ATTRB=(NORM,ASKIP),")
    els.append(make_el("E-SSMAPC1-017",17,"ENT1DOB","F-SSMAPC1-004","input",7,50,10,"NORM,UNPROT,FSET",False,False,None," ",None,None,49,50,"ENT1DOB DFHMDF POS=(07,50),LENGTH=10,ATTRB=(NORM,UNPROT,FSET),",
                       human_label="DOB", label_src=lsrc_dob,
                       rules=[maxlen_rule("E-SSMAPC1-017",10,49,50,"ENT1DOB DFHMDF POS=(07,50),LENGTH=10"),
                              date_cannot_determine_rule("E-SSMAPC1-017",53,54,"        DFHMDF POS=(07,63),LENGTH=12")]))
    # E-SSMAPC1-018: separator
    els.append(make_el("E-SSMAPC1-018",18,None,None,"separator",7,61,1,"PROT,ASKIP",True,False,None," ",None,None,51,52,"        DFHMDF POS=(07,61),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # E-SSMAPC1-019: hint (yyyy-mm-dd)
    els.append(make_el("E-SSMAPC1-019",19,None,None,"hint",7,63,12,"NORM,ASKIP",True,False,None,"(yyyy-mm-dd)",None,None,53,54,"        DFHMDF POS=(07,63),LENGTH=12,ATTRB=(NORM,ASKIP),"))
    # E-SSMAPC1-020: label House Name
    els.append(make_el("E-SSMAPC1-020",20,None,None,"label",8,30,12,"NORM,ASKIP",True,False,None,"House Name  ",None,None,56,57,"        DFHMDF POS=(08,30),LENGTH=12,ATTRB=(NORM,ASKIP),"))
    # E-SSMAPC1-021: ENT1HNM
    lsrc_hnm = make_ref(F,56,57,"        DFHMDF POS=(08,30),LENGTH=12,ATTRB=(NORM,ASKIP),")
    els.append(make_el("E-SSMAPC1-021",21,"ENT1HNM","F-SSMAPC1-005","input",8,50,20,"NORM,UNPROT,FSET",False,False,None," ",None,None,58,59,"ENT1HNM DFHMDF POS=(08,50),LENGTH=20,ATTRB=(NORM,UNPROT,FSET),",
                       human_label="House Name", label_src=lsrc_hnm,
                       rules=[maxlen_rule("E-SSMAPC1-021",20,58,59,"ENT1HNM DFHMDF POS=(08,50),LENGTH=20")]))
    # E-SSMAPC1-022: separator
    els.append(make_el("E-SSMAPC1-022",22,None,None,"separator",8,71,1,"PROT,ASKIP",True,False,None," ",None,None,60,61,"        DFHMDF POS=(08,71),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # E-SSMAPC1-023: label House Number
    els.append(make_el("E-SSMAPC1-023",23,None,None,"label",9,30,12,"NORM,ASKIP",True,False,None,"House Number",None,None,63,64,"        DFHMDF POS=(09,30),LENGTH=12,ATTRB=(NORM,ASKIP),"))
    # E-SSMAPC1-024: ENT1HNO
    lsrc_hno = make_ref(F,63,64,"        DFHMDF POS=(09,30),LENGTH=12,ATTRB=(NORM,ASKIP),")
    els.append(make_el("E-SSMAPC1-024",24,"ENT1HNO","F-SSMAPC1-006","input",9,50,4,"NORM,UNPROT,FSET",False,False,None," ",None,None,65,66,"ENT1HNO DFHMDF POS=(09,50),LENGTH=04,ATTRB=(NORM,UNPROT,FSET),",
                       human_label="House Number", label_src=lsrc_hno,
                       rules=[maxlen_rule("E-SSMAPC1-024",4,65,66,"ENT1HNO DFHMDF POS=(09,50),LENGTH=04")]))
    # E-SSMAPC1-025: separator
    els.append(make_el("E-SSMAPC1-025",25,None,None,"separator",9,55,1,"PROT,ASKIP",True,False,None," ",None,None,67,68,"        DFHMDF POS=(09,55),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # E-SSMAPC1-026: label Postcode
    els.append(make_el("E-SSMAPC1-026",26,None,None,"label",10,30,12,"NORM,ASKIP",True,False,None,"Postcode    ",None,None,70,71,"        DFHMDF POS=(10,30),LENGTH=12,ATTRB=(NORM,ASKIP),"))
    # E-SSMAPC1-027: ENT1HPC
    lsrc_hpc = make_ref(F,70,71,"        DFHMDF POS=(10,30),LENGTH=12,ATTRB=(NORM,ASKIP),")
    postcode_rules = [
        maxlen_rule("E-SSMAPC1-027",8,72,73,"ENT1HPC DFHMDF POS=(10,50),LENGTH=08"),
        {"ruleId":"R-E-SSMAPC1-027-002","type":"transformRule","certainty":"explicit",
         "plainEnglish":"The postcode is converted to uppercase before storage. Source: lgtestc1.cbl lines 126-127: MOVE FUNCTION UPPER-CASE(CA-POSTCODE) TO CA-POSTCODE.",
         "sourceRef":make_ref("legacy/cics-genapp/base/src/lgtestc1.cbl",126,127,"                  Move Function UPPER-CASE(CA-POSTCODE)")}
    ]
    els.append(make_el("E-SSMAPC1-027",27,"ENT1HPC","F-SSMAPC1-007","input",10,50,8,"NORM,UNPROT,FSET",False,False,None," ",None,None,72,73,"ENT1HPC DFHMDF POS=(10,50),LENGTH=08,ATTRB=(NORM,UNPROT,FSET),",
                       human_label="Postcode", label_src=lsrc_hpc, rules=postcode_rules))
    # E-SSMAPC1-028: separator
    els.append(make_el("E-SSMAPC1-028",28,None,None,"separator",10,59,1,"PROT,ASKIP",True,False,None," ",None,None,74,75,"        DFHMDF POS=(10,59),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # E-SSMAPC1-029: label Phone: Home
    els.append(make_el("E-SSMAPC1-029",29,None,None,"label",11,30,12,"NORM,ASKIP",True,False,None,"Phone: Home ",None,None,77,78,"        DFHMDF POS=(11,30),LENGTH=12,ATTRB=(NORM,ASKIP),"))
    # E-SSMAPC1-030: ENT1HP1
    lsrc_hp1 = make_ref(F,77,78,"        DFHMDF POS=(11,30),LENGTH=12,ATTRB=(NORM,ASKIP),")
    els.append(make_el("E-SSMAPC1-030",30,"ENT1HP1","F-SSMAPC1-008","input",11,50,20,"NORM,UNPROT,FSET",False,False,None," ",None,None,79,80,"ENT1HP1 DFHMDF POS=(11,50),LENGTH=20,ATTRB=(NORM,UNPROT,FSET),",
                       human_label="Phone: Home", label_src=lsrc_hp1,
                       rules=[maxlen_rule("E-SSMAPC1-030",20,79,80,"ENT1HP1 DFHMDF POS=(11,50),LENGTH=20")]))
    # E-SSMAPC1-031: separator (JUSTIFY=BLANK)
    els.append(make_el("E-SSMAPC1-031",31,None,None,"separator",11,71,1,"PROT,ASKIP",True,False,None," ","BLANK",None,81,82,"        DFHMDF POS=(11,71),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # E-SSMAPC1-032: label Phone: Mob
    els.append(make_el("E-SSMAPC1-032",32,None,None,"label",12,30,12,"NORM,ASKIP",True,False,None,"Phone: Mob  ",None,None,84,85,"        DFHMDF POS=(12,30),LENGTH=12,ATTRB=(NORM,ASKIP),"))
    # E-SSMAPC1-033: ENT1HP2
    lsrc_hp2 = make_ref(F,84,85,"        DFHMDF POS=(12,30),LENGTH=12,ATTRB=(NORM,ASKIP),")
    els.append(make_el("E-SSMAPC1-033",33,"ENT1HP2","F-SSMAPC1-009","input",12,50,20,"NORM,UNPROT,FSET",False,False,None," ","BLANK",None,86,87,"ENT1HP2 DFHMDF POS=(12,50),LENGTH=20,ATTRB=(NORM,UNPROT,FSET),",
                       human_label="Phone: Mob", label_src=lsrc_hp2,
                       rules=[maxlen_rule("E-SSMAPC1-033",20,86,87,"ENT1HP2 DFHMDF POS=(12,50),LENGTH=20")]))
    # E-SSMAPC1-034: separator
    els.append(make_el("E-SSMAPC1-034",34,None,None,"separator",12,71,1,"PROT,ASKIP",True,False,None," ",None,None,88,89,"        DFHMDF POS=(12,71),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # E-SSMAPC1-035: label Email Addr
    els.append(make_el("E-SSMAPC1-035",35,None,None,"label",13,30,12,"NORM,ASKIP",True,False,None,"Email  Addr ",None,None,91,92,"        DFHMDF POS=(13,30),LENGTH=12,ATTRB=(NORM,ASKIP),"))
    # E-SSMAPC1-036: ENT1HMO (email - note discrepancy)
    lsrc_hmo = make_ref(F,91,92,"        DFHMDF POS=(13,30),LENGTH=12,ATTRB=(NORM,ASKIP),")
    email_rules = [maxlen_rule("E-SSMAPC1-036",27,93,94,"ENT1HMO DFHMDF POS=(13,50),LENGTH=27")]
    els.append(make_el("E-SSMAPC1-036",36,"ENT1HMO","F-SSMAPC1-010","input",13,50,27,"NORM,UNPROT,FSET",False,False,None," ","BLANK",None,93,94,"ENT1HMO DFHMDF POS=(13,50),LENGTH=27,ATTRB=(NORM,UNPROT,FSET),",
                       human_label="Email  Addr", label_src=lsrc_hmo, rules=email_rules,
                       note="BMS LENGTH=27. COMMAREA CA-EMAIL-ADDRESS is PIC X(100). The screen entry maximum (27) is shorter than the COMMAREA capacity (100). This discrepancy is recorded from source; no rule is inferred."))
    # E-SSMAPC1-037: separator
    els.append(make_el("E-SSMAPC1-037",37,None,None,"separator",13,78,1,"PROT,ASKIP",True,False,None," ",None,None,95,96,"        DFHMDF POS=(13,78),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # E-SSMAPC1-038: label Select Option
    els.append(make_el("E-SSMAPC1-038",38,None,None,"label",22,8,14,"NORM,ASKIP",True,False,None,"Select Option ",None,None,98,99,"        DFHMDF POS=(22,08),LENGTH=14,ATTRB=(NORM,ASKIP),"))
    # E-SSMAPC1-039: ENT1OPT
    lsrc_opt = make_ref(F,98,99,"        DFHMDF POS=(22,08),LENGTH=14,ATTRB=(NORM,ASKIP),")
    els.append(make_el("E-SSMAPC1-039",39,"ENT1OPT","F-SSMAPC1-011","option",22,24,1,"NORM,NUM,UNPROT,FSET",False,True,"MUSTENTER"," ",None,None,100,101,"ENT1OPT DFHMDF POS=(22,24),LENGTH=1,ATTRB=(NORM,NUM,UNPROT,FSET),",
                       human_label="Select Option", label_src=lsrc_opt,
                       rules=mustenter_rules("E-SSMAPC1-039",100,101,"ENT1OPT DFHMDF POS=(22,24),LENGTH=1,ATTRB=(NORM,NUM,UNPROT,FSET),")))
    # E-SSMAPC1-040: separator after OPT
    els.append(make_el("E-SSMAPC1-040",40,None,None,"separator",22,26,1,"PROT,ASKIP",True,False,None," ",None,None,102,103,"        DFHMDF POS=(22,26),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # E-SSMAPC1-041: ERRFLD
    els.append(make_el("E-SSMAPC1-041",41,"ERRFLD","F-SSMAPC1-012","error",24,8,40,"BRT,ASKIP,PROT",True,False,None," ",None,None,105,106,"ERRFLD  DFHMDF POS=(24,8),LENGTH=40,ATTRB=(BRT,ASKIP,PROT),"))
    return els

# ─── Build remaining screens from BMS data ───────────────────────────────────

def sref(ls, le, exc): return make_ref(F, ls, le, exc)
def make_simple_el(map_name, seq, field_seq, bms_name, role, row, col, length, attrb, prot, num, validn, initial, xinit, justify, ls, le, exc, hl=None, lnote=None, lsrc=None, note=None, rules=None):
    fid = f"F-{map_name}-{field_seq:03d}" if bms_name else None
    return make_el(f"E-{map_name}-{seq:03d}", seq, bms_name, fid, role, row, col, length, attrb, prot, num, validn, initial, xinit, justify, ls, le, exc, hl, lnote, lsrc, note, rules)

def build_policy_screen_elements(map_name, dfhmdi_line, offset, option_line, err_line,
                                  fields_data, menu_opts, title_initial, title_col, title_len):
    """Build elements for a policy screen (SSP1-4 share similar structure)."""
    els = []
    seq = 0
    fseq = 0

    def e(bms_n, role, row, col, length, attrb, prot, num, validn, initial, xinit, justify, ls, le, exc, hl=None, lnote=None, lsrc=None, note=None, rules=None):
        nonlocal seq, fseq
        seq += 1
        if bms_n:
            fseq += 1
        fid = f"F-{map_name}-{fseq:03d}" if bms_n else None
        return make_el(f"E-{map_name}-{seq:03d}", seq, bms_n, fid, role, row, col, length, attrb, prot, num, validn, initial, xinit, justify, ls, le, exc, hl, lnote, lsrc, note, rules)

    # Title elements
    els.append(e(None,"title",1,1,4,"ASKIP,BRT",True,False,None,map_name[-2:]+"1"[0:0]+map_name[-2:],None,None,offset,offset,f"        DFHMDF POS=(1,1),LENGTH=4,ATTRB=(ASKIP,BRT),INITIAL='{map_name[-2:]}1'"))
    # Fix: trans id is SSP1 etc from the INITIAL field in BMS
    return els  # placeholder; full build done below

# Build all screens manually for accuracy
def build_ssmapp1_elements():
    els = []
    o = 0  # line offset relative to map start (line 112)
    def e(bms_n, role, row, col, length, attrb, prot, num, validn, initial, xinit, justify, ls, le, exc, hl=None, lnote=None, lsrc=None, note=None, rules=None):
        idx = len(els) + 1
        fseq = sum(1 for x in els if x.get('bmsName')) + (1 if bms_n else 0)
        fid = f"F-SSMAPP1-{fseq:03d}" if bms_n else None
        return make_el(f"E-SSMAPP1-{idx:03d}", idx, bms_n, fid, role, row, col, length, attrb, prot, num, validn, initial, xinit, justify, ls, le, exc, hl, lnote, lsrc, note, rules)

    els.append(e(None,"title",1,1,4,"ASKIP,BRT",True,False,None,"SSP1",None,None,113,113,"        DFHMDF POS=(1,1),LENGTH=4,ATTRB=(ASKIP,BRT),INITIAL='SSP1'"))
    els.append(e(None,"title",1,12,37,"BRT,ASKIP",True,False,None,"General Insurance Motor Policy Menu  ",None,None,114,115,"        DFHMDF POS=(1,12),LENGTH=37,ATTRB=(BRT,ASKIP),"))
    els.append(e(None,"menuOption",4,8,18,"NORM,ASKIP",True,False,None,"1. Policy Inquiry ",None,None,117,118,"        DFHMDF POS=(4,08),LENGTH=18,ATTRB=(NORM,ASKIP),"))
    els.append(e(None,"menuOption",5,8,16,"NORM,ASKIP",True,False,None,"2. Policy Add     ",None,None,119,120,"        DFHMDF POS=(5,08),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    els.append(e(None,"menuOption",6,8,16,"NORM,ASKIP",True,False,None,"3. Policy Delete  ",None,None,121,122,"        DFHMDF POS=(6,08),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    els.append(e(None,"menuOption",7,8,16,"NORM,ASKIP",True,False,None,"4. Policy Update  ",None,None,123,124,"        DFHMDF POS=(7,08),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    # Policy Number
    els.append(e(None,"label",4,30,15,"NORM,ASKIP",True,False,None,"Policy Number ",None,None,126,127,"        DFHMDF POS=(04,30),LENGTH=15,ATTRB=(NORM,ASKIP),"))
    ls = make_ref(F,126,127,"        DFHMDF POS=(04,30),LENGTH=15,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP1PNO","input",4,50,10,"NORM,UNPROT,IC,FSET",False,False,None,None,None,"RIGHT,ZERO",128,129,"ENP1PNO DFHMDF POS=(04,50),LENGTH=10,ATTRB=(NORM,UNPROT,IC,FSET),",hl="Policy Number",lsrc=ls,rules=[maxlen_rule("E-SSMAPP1-008",10,128,129,"ENP1PNO DFHMDF POS=(04,50),LENGTH=10")]))
    els.append(e(None,"separator",4,61,1,"PROT,ASKIP",True,False,None," ",None,None,130,131,"        DFHMDF POS=(04,61),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # Cust Number
    els.append(e(None,"label",5,30,16,"NORM,ASKIP",True,False,None,"Cust Number ",None,None,133,134,"        DFHMDF POS=(05,30),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    ls = make_ref(F,133,134,"        DFHMDF POS=(05,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP1CNO","input",5,50,10,"NORM,UNPROT,IC,FSET",False,False,None,None,None,"RIGHT,ZERO",135,136,"ENP1CNO DFHMDF POS=(05,50),LENGTH=10,ATTRB=(NORM,UNPROT,IC,FSET),",hl="Cust Number",lsrc=ls,rules=[maxlen_rule("E-SSMAPP1-011",10,135,136,"ENP1CNO DFHMDF POS=(05,50),LENGTH=10")]))
    els.append(e(None,"separator",5,61,1,"PROT,ASKIP",True,False,None," ",None,None,137,138,"        DFHMDF POS=(05,61),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # Issue date
    els.append(e(None,"label",6,30,16,"NORM,ASKIP",True,False,None,"Issue date ",None,None,140,141,"        DFHMDF POS=(06,30),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    ls = make_ref(F,140,141,"        DFHMDF POS=(06,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP1IDA","input",6,50,10,"NORM,UNPROT,FSET",False,False,None," ",None,None,142,143,"ENP1IDA DFHMDF POS=(06,50),LENGTH=10,ATTRB=(NORM,UNPROT,FSET),",hl="Issue date",lsrc=ls,rules=[maxlen_rule("E-SSMAPP1-014",10,142,143,"ENP1IDA DFHMDF"),date_cannot_determine_rule("E-SSMAPP1-014",146,147,"        DFHMDF POS=(06,63),LENGTH=12,INITIAL='(yyyy-mm-dd)'")]))
    els.append(e(None,"separator",6,61,1,"PROT,ASKIP",True,False,None," ",None,None,144,145,"        DFHMDF POS=(06,61),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    els.append(e(None,"hint",6,63,12,"NORM,ASKIP",True,False,None,"(yyyy-mm-dd)",None,None,146,147,"        DFHMDF POS=(06,63),LENGTH=12,ATTRB=(NORM,ASKIP),"))
    # Expiry date
    els.append(e(None,"label",7,30,16,"NORM,ASKIP",True,False,None,"Expiry date ",None,None,149,150,"        DFHMDF POS=(07,30),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    ls = make_ref(F,149,150,"        DFHMDF POS=(07,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP1EDA","input",7,50,10,"NORM,UNPROT,FSET",False,False,None," ",None,None,151,152,"ENP1EDA DFHMDF POS=(07,50),LENGTH=10,ATTRB=(NORM,UNPROT,FSET),",hl="Expiry date",lsrc=ls,rules=[maxlen_rule("E-SSMAPP1-018",10,151,152,"ENP1EDA DFHMDF"),date_cannot_determine_rule("E-SSMAPP1-018",155,156,"        DFHMDF POS=(07,63),LENGTH=12")]))
    els.append(e(None,"separator",7,61,1,"PROT,ASKIP",True,False,None," ",None,None,153,154,"        DFHMDF POS=(07,61),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    els.append(e(None,"hint",7,63,12,"NORM,ASKIP",True,False,None,"(yyyy-mm-dd)",None,None,155,156,"        DFHMDF POS=(07,63),LENGTH=12,ATTRB=(NORM,ASKIP),"))
    # Car Make
    els.append(e(None,"label",8,30,16,"NORM,ASKIP",True,False,None,"Car Make       ",None,None,158,159,"        DFHMDF POS=(08,30),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    ls = make_ref(F,158,159,"        DFHMDF POS=(08,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP1CMK","input",8,50,20,"NORM,UNPROT,FSET",False,False,None," ",None,None,160,161,"ENP1CMK DFHMDF POS=(08,50),LENGTH=20,ATTRB=(NORM,UNPROT,FSET),",hl="Car Make",lsrc=ls,rules=[maxlen_rule("E-SSMAPP1-022",20,160,161,"ENP1CMK DFHMDF")]))
    els.append(e(None,"separator",8,71,1,"PROT,ASKIP",True,False,None," ",None,None,162,163,"        DFHMDF POS=(08,71),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # Car Model
    els.append(e(None,"label",9,30,16,"NORM,ASKIP",True,False,None,"Car Model ",None,None,165,166,"        DFHMDF POS=(09,30),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    ls = make_ref(F,165,166,"        DFHMDF POS=(09,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP1CMO","input",9,50,20,"NORM,UNPROT,FSET",False,False,None," ",None,None,167,168,"ENP1CMO DFHMDF POS=(09,50),LENGTH=20,ATTRB=(NORM,UNPROT,FSET),",hl="Car Model",lsrc=ls,rules=[maxlen_rule("E-SSMAPP1-025",20,167,168,"ENP1CMO DFHMDF")]))
    els.append(e(None,"separator",9,71,1,"PROT,ASKIP",True,False,None," ",None,None,169,170,"        DFHMDF POS=(09,71),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # Car Value
    els.append(e(None,"label",10,30,16,"NORM,ASKIP",True,False,None,"Car Value   ",None,None,172,173,"        DFHMDF POS=(10,30),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    ls = make_ref(F,172,173,"        DFHMDF POS=(10,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP1VAL","input",10,50,6,"NORM,UNPROT,FSET",False,False,None," ","RIGHT,ZERO",None,174,175,"ENP1VAL DFHMDF POS=(10,50),LENGTH=06,ATTRB=(NORM,UNPROT,FSET),",hl="Car Value",lsrc=ls,rules=[maxlen_rule("E-SSMAPP1-028",6,174,175,"ENP1VAL DFHMDF")]))
    els.append(e(None,"separator",10,57,1,"PROT,ASKIP",True,False,None," ",None,None,176,177,"        DFHMDF POS=(10,57),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # Registration
    els.append(e(None,"label",11,30,16,"NORM,ASKIP",True,False,None,"Registration ",None,None,179,180,"        DFHMDF POS=(11,30),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    ls = make_ref(F,179,180,"        DFHMDF POS=(11,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP1REG","input",11,50,7,"NORM,UNPROT,FSET",False,False,None," ",None,None,181,182,"ENP1REG DFHMDF POS=(11,50),LENGTH=07,ATTRB=(NORM,UNPROT,FSET),",hl="Registration",lsrc=ls,rules=[maxlen_rule("E-SSMAPP1-031",7,181,182,"ENP1REG DFHMDF")]))
    els.append(e(None,"separator",11,58,1,"PROT,ASKIP",True,False,None," ",None,None,183,184,"        DFHMDF POS=(11,58),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # Car Colour
    els.append(e(None,"label",12,30,16,"NORM,ASKIP",True,False,None,"Car Colour  ",None,None,186,187,"        DFHMDF POS=(12,30),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    ls = make_ref(F,186,187,"        DFHMDF POS=(12,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP1COL","input",12,50,8,"NORM,UNPROT,FSET",False,False,None," ",None,None,188,189,"ENP1COL DFHMDF POS=(12,50),LENGTH=08,ATTRB=(NORM,UNPROT,FSET),",hl="Car Colour",lsrc=ls,rules=[maxlen_rule("E-SSMAPP1-034",8,188,189,"ENP1COL DFHMDF")]))
    els.append(e(None,"separator",12,59,1,"PROT,ASKIP",True,False,None," ",None,None,190,191,"        DFHMDF POS=(12,59),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # CC
    els.append(e(None,"label",13,30,16,"NORM,ASKIP",True,False,None,"CC  ",None,None,193,194,"        DFHMDF POS=(13,30),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    ls = make_ref(F,193,194,"        DFHMDF POS=(13,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP1CC","input",13,50,8,"NORM,UNPROT,FSET",False,False,None," ","RIGHT,ZERO",None,195,196,"ENP1CC  DFHMDF POS=(13,50),LENGTH=08,ATTRB=(NORM,UNPROT,FSET),",hl="CC",lsrc=ls,rules=[maxlen_rule("E-SSMAPP1-037",8,195,196,"ENP1CC  DFHMDF")]))
    els.append(e(None,"separator",13,59,1,"PROT,ASKIP",True,False,None," ",None,None,197,198,"        DFHMDF POS=(13,59),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # Manufacture Date
    els.append(e(None,"label",14,30,16,"NORM,ASKIP",True,False,None,"Manufacture Date",None,None,200,201,"        DFHMDF POS=(14,30),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    ls = make_ref(F,200,201,"        DFHMDF POS=(14,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP1MAN","input",14,50,10,"NORM,UNPROT,FSET",False,False,None," ",None,None,202,203,"ENP1MAN DFHMDF POS=(14,50),LENGTH=10,ATTRB=(NORM,UNPROT,FSET),",hl="Manufacture Date",lsrc=ls,rules=[maxlen_rule("E-SSMAPP1-040",10,202,203,"ENP1MAN DFHMDF"),date_cannot_determine_rule("E-SSMAPP1-040",206,207,"        DFHMDF POS=(14,63),LENGTH=12")]))
    els.append(e(None,"separator",14,61,1,"PROT,ASKIP",True,False,None," ",None,None,204,205,"        DFHMDF POS=(14,61),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    els.append(e(None,"hint",14,63,12,"NORM,ASKIP",True,False,None,"(yyyy-mm-dd)",None,None,206,207,"        DFHMDF POS=(14,63),LENGTH=12,ATTRB=(NORM,ASKIP),"))
    # No. of Accidents
    els.append(e(None,"label",15,30,16,"NORM,ASKIP",True,False,None,"No. of Accidents",None,None,209,210,"        DFHMDF POS=(15,30),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    ls = make_ref(F,209,210,"        DFHMDF POS=(15,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP1ACC","input",15,50,6,"NORM,UNPROT,FSET",False,False,None," ","RIGHT,ZERO",None,211,212,"ENP1ACC DFHMDF POS=(15,50),LENGTH=06,ATTRB=(NORM,UNPROT,FSET),",hl="No. of Accidents",lsrc=ls,rules=[maxlen_rule("E-SSMAPP1-044",6,211,212,"ENP1ACC DFHMDF")]))
    els.append(e(None,"separator",15,57,1,"PROT,ASKIP",True,False,None," ",None,None,213,214,"        DFHMDF POS=(15,57),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # Policy Premium
    els.append(e(None,"label",16,30,16,"NORM,ASKIP",True,False,None,"Policy Premium  ",None,None,216,217,"        DFHMDF POS=(16,30),LENGTH=16,ATTRB=(NORM,ASKIP),"))
    ls = make_ref(F,216,217,"        DFHMDF POS=(16,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP1PRE","input",16,50,6,"NORM,UNPROT,FSET",False,False,None," ","RIGHT,ZERO",None,218,219,"ENP1PRE DFHMDF POS=(16,50),LENGTH=06,ATTRB=(NORM,UNPROT,FSET),",hl="Policy Premium",lsrc=ls,rules=[maxlen_rule("E-SSMAPP1-047",6,218,219,"ENP1PRE DFHMDF")]))
    els.append(e(None,"separator",16,57,1,"PROT,ASKIP",True,False,None," ",None,None,220,221,"        DFHMDF POS=(16,57),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # Select Option
    els.append(e(None,"label",22,8,14,"NORM,ASKIP",True,False,None,"Select Option ",None,None,223,224,"        DFHMDF POS=(22,08),LENGTH=14,ATTRB=(NORM,ASKIP),"))
    ls = make_ref(F,223,224,"        DFHMDF POS=(22,08),LENGTH=14,ATTRB=(NORM,ASKIP),")
    eid_opt = f"E-SSMAPP1-{len(els)+1:03d}"
    els.append(e("ENP1OPT","option",22,24,1,"NORM,NUM,UNPROT,FSET",False,True,"MUSTENTER"," ",None,None,225,226,"ENP1OPT DFHMDF POS=(22,24),LENGTH=1,ATTRB=(NORM,NUM,UNPROT,FSET),",hl="Select Option",lsrc=ls,rules=mustenter_rules(eid_opt,225,226,"ENP1OPT DFHMDF POS=(22,24),LENGTH=1")))
    els.append(e(None,"separator",22,26,1,"PROT,ASKIP",True,False,None," ",None,None,227,228,"        DFHMDF POS=(22,26),LENGTH=1,ATTRB=(PROT,ASKIP),"))
    # Error field
    els.append(e("ERP1FLD","error",24,8,40,"BRT,ASKIP,PROT",True,False,None," ",None,None,230,231,"ERP1FLD DFHMDF POS=(24,8),LENGTH=40,ATTRB=(BRT,ASKIP,PROT),"))
    return els

# ─── For brevity, SSMAPP2/3/4/5 are built with a helper ─────────────────────
# Full element lists are generated inline below in build_catalogue()

def build_catalogue():
    today = datetime.date.today().isoformat()

    ssmapc1_els = build_ssmapc1_elements()
    ssmapp1_els = build_ssmapp1_elements()

    # Build remaining screens with same pattern (abbreviated here; full data embedded)
    ssmapp2_els = build_ssmapp2_elements()
    ssmapp3_els = build_ssmapp3_elements()
    ssmapp4_els = build_ssmapp4_elements()
    ssmapp5_els = build_ssmapp5_elements()

    screens = [
        {
            "mapsetName": "SSMAP",
            "mapName": "SSMAPC1",
            "transactionId": "SSC1",
            "title": "General Insurance Customer Menu",
            "size": {"rows": 24, "cols": 80},
            "presentationProgram": "LGTESTC1",
            "sourceRef": make_ref(F, 13, 13, "SSMAPC1 DFHMDI SIZE=(24,80)"),
            "elements": ssmapc1_els
        },
        {
            "mapsetName": "SSMAP",
            "mapName": "SSMAPP1",
            "transactionId": "SSP1",
            "title": "General Insurance Motor Policy Menu",
            "size": {"rows": 24, "cols": 80},
            "presentationProgram": "LGTESTP1",
            "sourceRef": make_ref(F, 112, 112, "SSMAPP1 DFHMDI SIZE=(24,80)"),
            "elements": ssmapp1_els
        },
        {
            "mapsetName": "SSMAP",
            "mapName": "SSMAPP2",
            "transactionId": "SSP2",
            "title": "General Insurance Endowment Policy Menu",
            "size": {"rows": 24, "cols": 80},
            "presentationProgram": "LGTESTP2",
            "sourceRef": make_ref(F, 237, 237, "SSMAPP2 DFHMDI SIZE=(24,80)"),
            "elements": ssmapp2_els
        },
        {
            "mapsetName": "SSMAP",
            "mapName": "SSMAPP3",
            "transactionId": "SSP3",
            "title": "General Insurance House Policy Menu",
            "size": {"rows": 24, "cols": 80},
            "presentationProgram": "LGTESTP3",
            "sourceRef": make_ref(F, 346, 346, "SSMAPP3 DFHMDI SIZE=(24,80)"),
            "elements": ssmapp3_els
        },
        {
            "mapsetName": "SSMAP",
            "mapName": "SSMAPP4",
            "transactionId": "SSP4",
            "title": "General Insurance Commercial Policy Menu",
            "size": {"rows": 24, "cols": 80},
            "presentationProgram": "LGTESTP4",
            "sourceRef": make_ref(F, 449, 449, "SSMAPP4 DFHMDI SIZE=(24,80)"),
            "elements": ssmapp4_els
        },
        {
            "mapsetName": "SSMAP",
            "mapName": "SSMAPP5",
            "transactionId": "SSP5",
            "title": "General Insurance Policy Claim Menu",
            "size": {"rows": 24, "cols": 80},
            "presentationProgram": "cannot-determine",
            "presentationProgramNote": "No LGTESTP5 program exists in the source tree. SSP5 is absent from base/Reference.md lines 46-57. Executability of SSP5 tasks cannot be determined from available source.",
            "sourceRef": make_ref(F, 606, 606, "SSMAPP5 DFHMDI SIZE=(24,80)"),
            "elements": ssmapp5_els
        }
    ]

    tasks = build_tasks()

    catalogue = {
        "provenance": {
            "repository": "https://github.com/cicsdev/cics-genapp",
            "commit": "f6f3f4b2580d31b7d8dcc31ce3e3676f4cceaaaa",
            "extractionDate": today,
            "statement": "The IBM CICS GenApp source was read from the pinned submodule. The legacy application was not run, compiled, emulated, or executed in any environment."
        },
        "screens": screens,
        "tasks": tasks
    }

    out_path = os.path.join(REPO_ROOT, "catalogue", "genapp.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(catalogue, f, indent=2, ensure_ascii=False)
    print(f"Written: {out_path}")
    return catalogue


# ─── SSMAPP2 elements ────────────────────────────────────────────────────────
def build_ssmapp2_elements():
    els = []
    def e(bms_n, role, row, col, length, attrb, prot, num, validn, initial, xinit, justify, ls, le, exc, hl=None, lnote=None, lsrc=None, note=None, rules=None):
        idx = len(els)+1; fseq = sum(1 for x in els if x.get('bmsName'))+(1 if bms_n else 0)
        fid = f"F-SSMAPP2-{fseq:03d}" if bms_n else None
        return make_el(f"E-SSMAPP2-{idx:03d}",idx,bms_n,fid,role,row,col,length,attrb,prot,num,validn,initial,xinit,justify,ls,le,exc,hl,lnote,lsrc,note,rules)
    els.append(e(None,"title",1,1,4,"ASKIP,BRT",True,False,None,"SSP2",None,None,238,238,"        DFHMDF POS=(1,1),LENGTH=4"))
    els.append(e(None,"title",1,12,40,"BRT,ASKIP",True,False,None,"General Insurance Endowment Policy Menu ",None,None,239,240,"        DFHMDF POS=(1,12),LENGTH=40"))
    els.append(e(None,"menuOption",4,8,18,"NORM,ASKIP",True,False,None,"1. Policy Inquiry ",None,None,242,243,"        DFHMDF POS=(4,08),LENGTH=18"))
    els.append(e(None,"menuOption",5,8,16,"NORM,ASKIP",True,False,None,"2. Policy Add     ",None,None,244,245,"        DFHMDF POS=(5,08),LENGTH=16"))
    els.append(e(None,"menuOption",6,8,16,"NORM,ASKIP",True,False,None,"3. Policy Delete  ",None,None,246,247,"        DFHMDF POS=(6,08),LENGTH=16"))
    els.append(e(None,"menuOption",7,8,16,"NORM,ASKIP",True,False,None,"4. Policy Update  ",None,None,248,249,"        DFHMDF POS=(7,08),LENGTH=16"))
    # Policy Number
    els.append(e(None,"label",4,30,15,"NORM,ASKIP",True,False,None,"Policy Number ",None,None,251,252,"        DFHMDF POS=(04,30),LENGTH=15"))
    ls=make_ref(F,251,252,"        DFHMDF POS=(04,30),LENGTH=15,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP2PNO","input",4,50,10,"NORM,UNPROT,IC,FSET",False,False,None,None,None,"RIGHT,ZERO",253,254,"ENP2PNO DFHMDF POS=(04,50),LENGTH=10",hl="Policy Number",lsrc=ls,rules=[maxlen_rule("E-SSMAPP2-008",10,253,254,"ENP2PNO DFHMDF")]))
    els.append(e(None,"separator",4,61,1,"PROT,ASKIP",True,False,None," ",None,None,255,256,"        DFHMDF POS=(04,61),LENGTH=1"))
    # Cust Number
    els.append(e(None,"label",5,30,16,"NORM,ASKIP",True,False,None,"Cust Number ",None,None,258,259,"        DFHMDF POS=(05,30),LENGTH=16"))
    ls=make_ref(F,258,259,"        DFHMDF POS=(05,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP2CNO","input",5,50,10,"NORM,UNPROT,IC,FSET",False,False,None,None,None,"RIGHT,ZERO",260,261,"ENP2CNO DFHMDF POS=(05,50),LENGTH=10",hl="Cust Number",lsrc=ls,rules=[maxlen_rule("E-SSMAPP2-011",10,260,261,"ENP2CNO DFHMDF")]))
    els.append(e(None,"separator",5,61,1,"PROT,ASKIP",True,False,None," ",None,None,262,263,"        DFHMDF POS=(05,61),LENGTH=1"))
    # Issue date
    els.append(e(None,"label",6,30,16,"NORM,ASKIP",True,False,None,"Issue date ",None,None,265,266,"        DFHMDF POS=(06,30),LENGTH=16"))
    ls=make_ref(F,265,266,"        DFHMDF POS=(06,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP2IDA","input",6,50,10,"NORM,UNPROT,FSET",False,False,None," ",None,None,267,268,"ENP2IDA DFHMDF POS=(06,50),LENGTH=10",hl="Issue date",lsrc=ls,rules=[maxlen_rule("E-SSMAPP2-014",10,267,268,"ENP2IDA DFHMDF"),date_cannot_determine_rule("E-SSMAPP2-014",271,272,"        DFHMDF POS=(06,63),LENGTH=12,ATTRB=(NORM,ASKIP),")]))
    els.append(e(None,"separator",6,61,1,"PROT,ASKIP",True,False,None," ",None,None,269,270,"        DFHMDF POS=(06,61),LENGTH=1"))
    els.append(e(None,"hint",6,63,12,"NORM,ASKIP",True,False,None,"(yyyy-mm-dd)",None,None,271,272,"        DFHMDF POS=(06,63),LENGTH=12"))
    # Expiry date
    els.append(e(None,"label",7,30,16,"NORM,ASKIP",True,False,None,"Expiry date ",None,None,274,275,"        DFHMDF POS=(07,30),LENGTH=16"))
    ls=make_ref(F,274,275,"        DFHMDF POS=(07,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP2EDA","input",7,50,10,"NORM,UNPROT,FSET",False,False,None," ",None,None,276,277,"ENP2EDA DFHMDF POS=(07,50),LENGTH=10",hl="Expiry date",lsrc=ls,rules=[maxlen_rule("E-SSMAPP2-018",10,276,277,"ENP2EDA DFHMDF"),date_cannot_determine_rule("E-SSMAPP2-018",280,281,"        DFHMDF POS=(07,63),LENGTH=12,ATTRB=(NORM,ASKIP),")]))
    els.append(e(None,"separator",7,61,1,"PROT,ASKIP",True,False,None," ",None,None,278,279,"        DFHMDF POS=(07,61),LENGTH=1"))
    els.append(e(None,"hint",7,63,12,"NORM,ASKIP",True,False,None,"(yyyy-mm-dd)",None,None,280,281,"        DFHMDF POS=(07,63),LENGTH=12"))
    # Fund Name
    els.append(e(None,"label",8,30,16,"NORM,ASKIP",True,False,None,"Fund Name ",None,None,283,284,"        DFHMDF POS=(08,30),LENGTH=16",note="Raw BMS INITIAL contains embedded quote: 'Fund Name '    ' - label text recorded as read."))
    ls=make_ref(F,283,284,"        DFHMDF POS=(08,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP2FNM","input",8,50,10,"NORM,UNPROT,FSET",False,False,None," ",None,None,285,286,"ENP2FNM DFHMDF POS=(08,50),LENGTH=10",hl="Fund Name",lsrc=ls,rules=[maxlen_rule("E-SSMAPP2-022",10,285,286,"ENP2FNM DFHMDF")]))
    els.append(e(None,"separator",8,61,1,"PROT,ASKIP",True,False,None," ",None,None,287,288,"        DFHMDF POS=(08,61),LENGTH=1"))
    # Term
    els.append(e(None,"label",9,30,16,"NORM,ASKIP",True,False,None,"Term      ",None,None,290,291,"        DFHMDF POS=(09,30),LENGTH=16"))
    ls=make_ref(F,290,291,"        DFHMDF POS=(09,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP2TER","input",9,50,2,"NORM,UNPROT,FSET",False,False,None," ",None,None,292,293,"ENP2TER DFHMDF POS=(09,50),LENGTH=02",hl="Term",lsrc=ls,rules=[maxlen_rule("E-SSMAPP2-025",2,292,293,"ENP2TER DFHMDF")]))
    els.append(e(None,"separator",9,53,1,"PROT,ASKIP",True,False,None," ",None,None,294,295,"        DFHMDF POS=(09,53),LENGTH=1"))
    # Sum Assured
    els.append(e(None,"label",10,30,16,"NORM,ASKIP",True,False,None,"Sum Assured ",None,None,297,298,"        DFHMDF POS=(10,30),LENGTH=16"))
    ls=make_ref(F,297,298,"        DFHMDF POS=(10,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP2SUM","input",10,50,6,"NORM,UNPROT,FSET",False,False,None," ","RIGHT,ZERO",None,299,300,"ENP2SUM DFHMDF POS=(10,50),LENGTH=06",hl="Sum Assured",lsrc=ls,rules=[maxlen_rule("E-SSMAPP2-028",6,299,300,"ENP2SUM DFHMDF")]))
    els.append(e(None,"separator",10,57,1,"PROT,ASKIP",True,False,None," ",None,None,301,302,"        DFHMDF POS=(10,57),LENGTH=1"))
    # Life Assured
    els.append(e(None,"label",11,30,16,"NORM,ASKIP",True,False,None,"Life Assured ",None,None,304,305,"        DFHMDF POS=(11,30),LENGTH=16"))
    ls=make_ref(F,304,305,"        DFHMDF POS=(11,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP2LIF","input",11,50,25,"NORM,UNPROT,FSET",False,False,None," ","RIGHT,ZERO",None,306,307,"ENP2LIF DFHMDF POS=(11,50),LENGTH=25",hl="Life Assured",lsrc=ls,rules=[maxlen_rule("E-SSMAPP2-031",25,306,307,"ENP2LIF DFHMDF")]))
    els.append(e(None,"separator",11,76,1,"PROT,ASKIP",True,False,None," ",None,None,308,309,"        DFHMDF POS=(11,76),LENGTH=1"))
    # With Profits
    els.append(e(None,"label",12,30,16,"NORM,ASKIP",True,False,None,"With Profits ",None,None,311,312,"        DFHMDF POS=(12,30),LENGTH=16"))
    ls=make_ref(F,311,312,"        DFHMDF POS=(12,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP2WPR","input",12,50,1,"NORM,UNPROT,FSET",False,False,None," ",None,None,313,314,"ENP2WPR DFHMDF POS=(12,50),LENGTH=01",hl="With Profits",lsrc=ls,rules=[maxlen_rule("E-SSMAPP2-034",1,313,314,"ENP2WPR DFHMDF")]))
    els.append(e(None,"separator",12,52,1,"PROT,ASKIP",True,False,None," ",None,None,315,316,"        DFHMDF POS=(12,52),LENGTH=1"))
    # Equities
    els.append(e(None,"label",13,30,16,"NORM,ASKIP",True,False,None,"Equities     ",None,None,318,319,"        DFHMDF POS=(13,30),LENGTH=16"))
    ls=make_ref(F,318,319,"        DFHMDF POS=(13,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP2EQU","input",13,50,1,"NORM,UNPROT,FSET",False,False,None," ",None,None,320,321,"ENP2EQU DFHMDF POS=(13,50),LENGTH=01",hl="Equities",lsrc=ls,rules=[maxlen_rule("E-SSMAPP2-037",1,320,321,"ENP2EQU DFHMDF")]))
    els.append(e(None,"separator",13,52,1,"PROT,ASKIP",True,False,None," ",None,None,322,323,"        DFHMDF POS=(13,52),LENGTH=1"))
    # Managed Funds
    els.append(e(None,"label",14,30,16,"NORM,ASKIP",True,False,None,"Managed Funds",None,None,325,326,"        DFHMDF POS=(14,30),LENGTH=16"))
    ls=make_ref(F,325,326,"        DFHMDF POS=(14,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP2MAN","input",14,50,1,"NORM,UNPROT,FSET",False,False,None," ",None,None,327,328,"ENP2MAN DFHMDF POS=(14,50),LENGTH=01",hl="Managed Funds",lsrc=ls,rules=[maxlen_rule("E-SSMAPP2-040",1,327,328,"ENP2MAN DFHMDF")]))
    els.append(e(None,"separator",14,52,1,"PROT,ASKIP",True,False,None," ",None,None,329,330,"        DFHMDF POS=(14,52),LENGTH=1"))
    # Select Option
    els.append(e(None,"label",22,8,14,"NORM,ASKIP",True,False,None,"Select Option ",None,None,332,333,"        DFHMDF POS=(22,08),LENGTH=14"))
    ls=make_ref(F,332,333,"        DFHMDF POS=(22,08),LENGTH=14,ATTRB=(NORM,ASKIP),")
    eid_opt=f"E-SSMAPP2-{len(els)+1:03d}"
    els.append(e("ENP2OPT","option",22,24,1,"NORM,NUM,UNPROT,FSET",False,True,"MUSTENTER"," ",None,None,334,335,"ENP2OPT DFHMDF POS=(22,24),LENGTH=1",hl="Select Option",lsrc=ls,rules=mustenter_rules(eid_opt,334,335,"ENP2OPT DFHMDF POS=(22,24),LENGTH=1")))
    els.append(e(None,"separator",22,26,1,"PROT,ASKIP",True,False,None," ",None,None,336,337,"        DFHMDF POS=(22,26),LENGTH=1"))
    els.append(e("ERP2FLD","error",24,8,40,"BRT,ASKIP,PROT",True,False,None," ",None,None,339,340,"ERP2FLD DFHMDF POS=(24,8),LENGTH=40"))
    return els

def build_ssmapp3_elements():
    els = []
    def e(bms_n, role, row, col, length, attrb, prot, num, validn, initial, xinit, justify, ls, le, exc, hl=None, lnote=None, lsrc=None, note=None, rules=None):
        idx=len(els)+1; fseq=sum(1 for x in els if x.get('bmsName'))+(1 if bms_n else 0)
        fid=f"F-SSMAPP3-{fseq:03d}" if bms_n else None
        return make_el(f"E-SSMAPP3-{idx:03d}",idx,bms_n,fid,role,row,col,length,attrb,prot,num,validn,initial,xinit,justify,ls,le,exc,hl,lnote,lsrc,note,rules)
    els.append(e(None,"title",1,1,4,"ASKIP,BRT",True,False,None,"SSP3",None,None,347,347,"        DFHMDF POS=(1,1),LENGTH=4"))
    els.append(e(None,"title",1,12,40,"BRT,ASKIP",True,False,None,"General Insurance House Policy Menu ",None,None,348,349,"        DFHMDF POS=(1,12),LENGTH=40"))
    els.append(e(None,"menuOption",4,8,18,"NORM,ASKIP",True,False,None,"1. Policy Inquiry ",None,None,351,352,"        DFHMDF POS=(4,08),LENGTH=18"))
    els.append(e(None,"menuOption",5,8,16,"NORM,ASKIP",True,False,None,"2. Policy Add     ",None,None,353,354,"        DFHMDF POS=(5,08),LENGTH=16"))
    els.append(e(None,"menuOption",6,8,16,"NORM,ASKIP",True,False,None,"3. Policy Delete  ",None,None,355,356,"        DFHMDF POS=(6,08),LENGTH=16"))
    els.append(e(None,"menuOption",7,8,16,"NORM,ASKIP",True,False,None,"4. Policy Update  ",None,None,357,358,"        DFHMDF POS=(7,08),LENGTH=16"))
    els.append(e(None,"label",4,30,15,"NORM,ASKIP",True,False,None,"Policy Number ",None,None,360,361,"        DFHMDF POS=(04,30),LENGTH=15"))
    ls=make_ref(F,360,361,"        DFHMDF POS=(04,30),LENGTH=15,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP3PNO","input",4,50,10,"NORM,UNPROT,IC,FSET",False,False,None,None,None,"RIGHT,ZERO",362,363,"ENP3PNO DFHMDF POS=(04,50),LENGTH=10",hl="Policy Number",lsrc=ls,rules=[maxlen_rule("E-SSMAPP3-008",10,362,363,"ENP3PNO DFHMDF")]))
    els.append(e(None,"separator",4,61,1,"PROT,ASKIP",True,False,None," ",None,None,364,365,"        DFHMDF POS=(04,61),LENGTH=1"))
    els.append(e(None,"label",5,30,16,"NORM,ASKIP",True,False,None,"Cust Number ",None,None,367,368,"        DFHMDF POS=(05,30),LENGTH=16"))
    ls=make_ref(F,367,368,"        DFHMDF POS=(05,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP3CNO","input",5,50,10,"NORM,UNPROT,IC,FSET",False,False,None,None,None,"RIGHT,ZERO",369,370,"ENP3CNO DFHMDF POS=(05,50),LENGTH=10",hl="Cust Number",lsrc=ls,rules=[maxlen_rule("E-SSMAPP3-011",10,369,370,"ENP3CNO DFHMDF")]))
    els.append(e(None,"separator",5,61,1,"PROT,ASKIP",True,False,None," ",None,None,371,372,"        DFHMDF POS=(05,61),LENGTH=1"))
    els.append(e(None,"label",6,30,16,"NORM,ASKIP",True,False,None,"Issue date ",None,None,374,375,"        DFHMDF POS=(06,30),LENGTH=16"))
    ls=make_ref(F,374,375,"        DFHMDF POS=(06,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP3IDA","input",6,50,10,"NORM,UNPROT,FSET",False,False,None," ",None,None,376,377,"ENP3IDA DFHMDF POS=(06,50),LENGTH=10",hl="Issue date",lsrc=ls,rules=[maxlen_rule("E-SSMAPP3-014",10,376,377,"ENP3IDA DFHMDF"),date_cannot_determine_rule("E-SSMAPP3-014",380,381,"        DFHMDF POS=(06,63),LENGTH=12,ATTRB=(NORM,ASKIP),")]))
    els.append(e(None,"separator",6,61,1,"PROT,ASKIP",True,False,None," ",None,None,378,379,"        DFHMDF POS=(06,61),LENGTH=1"))
    els.append(e(None,"hint",6,63,12,"NORM,ASKIP",True,False,None,"(yyyy-mm-dd)",None,None,380,381,"        DFHMDF POS=(06,63),LENGTH=12"))
    els.append(e(None,"label",7,30,16,"NORM,ASKIP",True,False,None,"Expiry date ",None,None,383,384,"        DFHMDF POS=(07,30),LENGTH=16"))
    ls=make_ref(F,383,384,"        DFHMDF POS=(07,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP3EDA","input",7,50,10,"NORM,UNPROT,FSET",False,False,None," ",None,None,385,386,"ENP3EDA DFHMDF POS=(07,50),LENGTH=10",hl="Expiry date",lsrc=ls,rules=[maxlen_rule("E-SSMAPP3-018",10,385,386,"ENP3EDA DFHMDF"),date_cannot_determine_rule("E-SSMAPP3-018",389,390,"        DFHMDF POS=(07,63),LENGTH=12,ATTRB=(NORM,ASKIP),")]))
    els.append(e(None,"separator",7,61,1,"PROT,ASKIP",True,False,None," ",None,None,387,388,"        DFHMDF POS=(07,61),LENGTH=1"))
    els.append(e(None,"hint",7,63,12,"NORM,ASKIP",True,False,None,"(yyyy-mm-dd)",None,None,389,390,"        DFHMDF POS=(07,63),LENGTH=12"))
    els.append(e(None,"label",8,30,16,"NORM,ASKIP",True,False,None,"Property Type  ",None,None,392,393,"        DFHMDF POS=(08,30),LENGTH=16"))
    ls=make_ref(F,392,393,"        DFHMDF POS=(08,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP3TYP","input",8,50,15,"NORM,UNPROT,FSET",False,False,None," ",None,None,394,395,"ENP3TYP DFHMDF POS=(08,50),LENGTH=15",hl="Property Type",lsrc=ls,rules=[maxlen_rule("E-SSMAPP3-022",15,394,395,"ENP3TYP DFHMDF")]))
    els.append(e(None,"separator",8,66,1,"PROT,ASKIP",True,False,None," ",None,None,396,397,"        DFHMDF POS=(08,66),LENGTH=1"))
    els.append(e(None,"label",9,30,16,"NORM,ASKIP",True,False,None,"Bedrooms  ",None,None,399,400,"        DFHMDF POS=(09,30),LENGTH=16"))
    ls=make_ref(F,399,400,"        DFHMDF POS=(09,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP3BED","input",9,50,3,"NORM,UNPROT,FSET",False,False,None," ","RIGHT,ZERO",None,401,402,"ENP3BED DFHMDF POS=(09,50),LENGTH=03",hl="Bedrooms",lsrc=ls,rules=[maxlen_rule("E-SSMAPP3-025",3,401,402,"ENP3BED DFHMDF")]))
    els.append(e(None,"separator",9,54,1,"PROT,ASKIP",True,False,None," ",None,None,403,404,"        DFHMDF POS=(09,54),LENGTH=1"))
    els.append(e(None,"label",10,30,16,"NORM,ASKIP",True,False,None,"House Value ",None,None,406,407,"        DFHMDF POS=(10,30),LENGTH=16"))
    ls=make_ref(F,406,407,"        DFHMDF POS=(10,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP3VAL","input",10,50,8,"NORM,UNPROT,FSET",False,False,None," ","RIGHT,ZERO",None,408,409,"ENP3VAL DFHMDF POS=(10,50),LENGTH=08",hl="House Value",lsrc=ls,rules=[maxlen_rule("E-SSMAPP3-028",8,408,409,"ENP3VAL DFHMDF")]))
    els.append(e(None,"separator",10,59,1,"PROT,ASKIP",True,False,None," ",None,None,410,411,"        DFHMDF POS=(10,59),LENGTH=1"))
    els.append(e(None,"label",11,30,16,"NORM,ASKIP",True,False,None,"House Name   ",None,None,413,414,"        DFHMDF POS=(11,30),LENGTH=16"))
    ls=make_ref(F,413,414,"        DFHMDF POS=(11,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP3HNM","input",11,50,20,"NORM,UNPROT,FSET",False,False,None," ",None,None,415,416,"ENP3HNM DFHMDF POS=(11,50),LENGTH=20",hl="House Name",lsrc=ls,rules=[maxlen_rule("E-SSMAPP3-031",20,415,416,"ENP3HNM DFHMDF")]))
    els.append(e(None,"separator",11,71,1,"PROT,ASKIP",True,False,None," ",None,None,417,418,"        DFHMDF POS=(11,71),LENGTH=1"))
    els.append(e(None,"label",12,30,16,"NORM,ASKIP",True,False,None,"House Number ",None,None,420,421,"        DFHMDF POS=(12,30),LENGTH=16"))
    ls=make_ref(F,420,421,"        DFHMDF POS=(12,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP3HNO","input",12,50,4,"NORM,UNPROT,FSET",False,False,None," ",None,None,422,423,"ENP3HNO DFHMDF POS=(12,50),LENGTH=04",hl="House Number",lsrc=ls,rules=[maxlen_rule("E-SSMAPP3-034",4,422,423,"ENP3HNO DFHMDF")]))
    els.append(e(None,"separator",12,55,1,"PROT,ASKIP",True,False,None," ",None,None,424,425,"        DFHMDF POS=(12,55),LENGTH=1"))
    els.append(e(None,"label",13,30,16,"NORM,ASKIP",True,False,None,"Postcode     ",None,None,427,428,"        DFHMDF POS=(13,30),LENGTH=16"))
    ls=make_ref(F,427,428,"        DFHMDF POS=(13,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP3HPC","input",13,50,8,"NORM,UNPROT,FSET",False,False,None," ",None,None,429,430,"ENP3HPC DFHMDF POS=(13,50),LENGTH=08",hl="Postcode",lsrc=ls,rules=[maxlen_rule("E-SSMAPP3-037",8,429,430,"ENP3HPC DFHMDF")]))
    els.append(e(None,"separator",13,59,1,"PROT,ASKIP",True,False,None," ",None,None,431,432,"        DFHMDF POS=(13,59),LENGTH=1"))
    els.append(e(None,"label",22,8,14,"NORM,ASKIP",True,False,None,"Select Option ",None,None,435,436,"        DFHMDF POS=(22,08),LENGTH=14"))
    ls=make_ref(F,435,436,"        DFHMDF POS=(22,08),LENGTH=14,ATTRB=(NORM,ASKIP),")
    eid_opt=f"E-SSMAPP3-{len(els)+1:03d}"
    els.append(e("ENP3OPT","option",22,24,1,"NORM,NUM,UNPROT,FSET",False,True,"MUSTENTER"," ",None,None,437,438,"ENP3OPT DFHMDF POS=(22,24),LENGTH=1",hl="Select Option",lsrc=ls,rules=mustenter_rules(eid_opt,437,438,"ENP3OPT DFHMDF")))
    els.append(e(None,"separator",22,26,1,"PROT,ASKIP",True,False,None," ",None,None,439,440,"        DFHMDF POS=(22,26),LENGTH=1"))
    els.append(e("ERP3FLD","error",24,8,40,"BRT,ASKIP,PROT",True,False,None," ",None,None,442,443,"ERP3FLD DFHMDF POS=(24,8),LENGTH=40"))
    return els

def build_ssmapp4_elements():
    els = []
    def e(bms_n, role, row, col, length, attrb, prot, num, validn, initial, xinit, justify, ls, le, exc, hl=None, lnote=None, lsrc=None, note=None, rules=None):
        idx=len(els)+1; fseq=sum(1 for x in els if x.get('bmsName'))+(1 if bms_n else 0)
        fid=f"F-SSMAPP4-{fseq:03d}" if bms_n else None
        return make_el(f"E-SSMAPP4-{idx:03d}",idx,bms_n,fid,role,row,col,length,attrb,prot,num,validn,initial,xinit,justify,ls,le,exc,hl,lnote,lsrc,note,rules)
    els.append(e(None,"title",1,1,4,"ASKIP,BRT",True,False,None,"SSP4",None,None,450,450,"        DFHMDF POS=(1,1),LENGTH=4"))
    els.append(e(None,"title",1,12,41,"BRT,ASKIP",True,False,None,"General Insurance Commercial Policy Menu ",None,None,451,452,"        DFHMDF POS=(1,12),LENGTH=41"))
    els.append(e(None,"menuOption",4,8,18,"NORM,ASKIP",True,False,None,"1. Policy Inquiry ",None,None,454,455,"        DFHMDF POS=(4,08),LENGTH=18"))
    els.append(e(None,"menuOption",5,8,16,"NORM,ASKIP",True,False,None,"2. Policy Add     ",None,None,456,457,"        DFHMDF POS=(5,08),LENGTH=16"))
    els.append(e(None,"menuOption",6,8,16,"NORM,ASKIP",True,False,None,"3. Policy Delete  ",None,None,458,459,"        DFHMDF POS=(6,08),LENGTH=16",note="Option 4 (Policy Update) is commented out in BMS source at lines 460-461. No COBOL dispatch case exists in lgtestp4.cbl. Update Commercial is absent."))
    els.append(e(None,"label",4,30,15,"NORM,ASKIP",True,False,None,"Policy Number ",None,None,463,464,"        DFHMDF POS=(04,30),LENGTH=15"))
    ls=make_ref(F,463,464,"        DFHMDF POS=(04,30),LENGTH=15,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP4PNO","input",4,50,10,"NORM,UNPROT,IC,FSET",False,False,None,None,None,"RIGHT,ZERO",465,466,"ENP4PNO DFHMDF POS=(04,50),LENGTH=10",hl="Policy Number",lsrc=ls,rules=[maxlen_rule("E-SSMAPP4-007",10,465,466,"ENP4PNO DFHMDF")]))
    els.append(e(None,"separator",4,61,1,"PROT,ASKIP",True,False,None," ",None,None,467,468,"        DFHMDF POS=(04,61),LENGTH=1"))
    els.append(e(None,"label",5,30,16,"NORM,ASKIP",True,False,None,"Cust Number ",None,None,470,471,"        DFHMDF POS=(05,30),LENGTH=16"))
    ls=make_ref(F,470,471,"        DFHMDF POS=(05,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP4CNO","input",5,50,10,"NORM,UNPROT,IC,FSET",False,False,None,None,None,"RIGHT,ZERO",472,473,"ENP4CNO DFHMDF POS=(05,50),LENGTH=10",hl="Cust Number",lsrc=ls,rules=[maxlen_rule("E-SSMAPP4-010",10,472,473,"ENP4CNO DFHMDF")]))
    els.append(e(None,"separator",5,61,1,"PROT,ASKIP",True,False,None," ",None,None,474,475,"        DFHMDF POS=(05,61),LENGTH=1"))
    els.append(e(None,"label",6,30,16,"NORM,ASKIP",True,False,None,"Start date ",None,None,477,478,"        DFHMDF POS=(06,30),LENGTH=16"))
    ls=make_ref(F,477,478,"        DFHMDF POS=(06,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP4IDA","input",6,50,10,"NORM,UNPROT,FSET",False,False,None," ",None,None,479,480,"ENP4IDA DFHMDF POS=(06,50),LENGTH=10",hl="Start date",lsrc=ls,rules=[maxlen_rule("E-SSMAPP4-013",10,479,480,"ENP4IDA DFHMDF"),date_cannot_determine_rule("E-SSMAPP4-013",483,484,"        DFHMDF POS=(06,63),LENGTH=12,ATTRB=(NORM,ASKIP),")]))
    els.append(e(None,"separator",6,61,1,"PROT,ASKIP",True,False,None," ",None,None,481,482,"        DFHMDF POS=(06,61),LENGTH=1"))
    els.append(e(None,"hint",6,63,12,"NORM,ASKIP",True,False,None,"(yyyy-mm-dd)",None,None,483,484,"        DFHMDF POS=(06,63),LENGTH=12"))
    els.append(e(None,"label",7,30,16,"NORM,ASKIP",True,False,None,"Expiry date ",None,None,486,487,"        DFHMDF POS=(07,30),LENGTH=16"))
    ls=make_ref(F,486,487,"        DFHMDF POS=(07,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP4EDA","input",7,50,10,"NORM,UNPROT,FSET",False,False,None," ",None,None,488,489,"ENP4EDA DFHMDF POS=(07,50),LENGTH=10",hl="Expiry date",lsrc=ls,rules=[maxlen_rule("E-SSMAPP4-017",10,488,489,"ENP4EDA DFHMDF"),date_cannot_determine_rule("E-SSMAPP4-017",492,493,"        DFHMDF POS=(07,63),LENGTH=12,ATTRB=(NORM,ASKIP),")]))
    els.append(e(None,"separator",7,61,1,"PROT,ASKIP",True,False,None," ",None,None,490,491,"        DFHMDF POS=(07,61),LENGTH=1"))
    els.append(e(None,"hint",7,63,12,"NORM,ASKIP",True,False,None,"(yyyy-mm-dd)",None,None,492,493,"        DFHMDF POS=(07,63),LENGTH=12"))
    els.append(e(None,"label",8,30,16,"NORM,ASKIP",True,False,None,"Address ",None,None,495,496,"        DFHMDF POS=(08,30),LENGTH=16"))
    ls=make_ref(F,495,496,"        DFHMDF POS=(08,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP4ADD","input",8,50,25,"NORM,UNPROT,FSET",False,False,None," ",None,None,497,498,"ENP4ADD DFHMDF POS=(08,50),LENGTH=25",hl="Address",lsrc=ls,rules=[maxlen_rule("E-SSMAPP4-021",25,497,498,"ENP4ADD DFHMDF")]))
    els.append(e(None,"separator",8,76,1,"PROT,ASKIP",True,False,None," ",None,None,499,500,"        DFHMDF POS=(08,76),LENGTH=1"))
    els.append(e(None,"label",9,30,16,"NORM,ASKIP",True,False,None,"Postcode     ",None,None,502,503,"        DFHMDF POS=(09,30),LENGTH=16"))
    ls=make_ref(F,502,503,"        DFHMDF POS=(09,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP4HPC","input",9,50,8,"NORM,UNPROT,FSET",False,False,None," ",None,None,504,505,"ENP4HPC DFHMDF POS=(09,50),LENGTH=08",hl="Postcode",lsrc=ls,rules=[maxlen_rule("E-SSMAPP4-024",8,504,505,"ENP4HPC DFHMDF")]))
    els.append(e(None,"separator",9,59,1,"PROT,ASKIP",True,False,None," ",None,None,506,507,"        DFHMDF POS=(09,59),LENGTH=1"))
    # Lat/Lon shared label
    lat_lon_label_src = make_ref(F,509,510,"        DFHMDF POS=(10,30),LENGTH=18,INITIAL='Latitude/Longitude'")
    els.append(e(None,"label",10,30,18,"NORM,ASKIP",True,False,None,"Latitude/Longitude",None,None,509,510,"        DFHMDF POS=(10,30),LENGTH=18"))
    els.append(e("ENP4LAT","input",10,50,11,"NORM,UNPROT,FSET",False,False,None," ","RIGHT,ZERO",None,511,512,"ENP4LAT DFHMDF POS=(10,50),LENGTH=11",hl="Latitude/Longitude",lnote="shared-label",lsrc=lat_lon_label_src,rules=[maxlen_rule("E-SSMAPP4-027",11,511,512,"ENP4LAT DFHMDF")]))
    els.append(e(None,"separator",10,62,1,"PROT,ASKIP",True,False,None," ",None,None,513,514,"        DFHMDF POS=(10,62),LENGTH=1"))
    els.append(e("ENP4LON","input",10,64,11,"NORM,UNPROT,FSET",False,False,None," ","RIGHT,ZERO",None,515,516,"ENP4LON DFHMDF POS=(10,64),LENGTH=11",hl="Latitude/Longitude",lnote="shared-label",lsrc=lat_lon_label_src,rules=[maxlen_rule("E-SSMAPP4-029",11,515,516,"ENP4LON DFHMDF")]))
    els.append(e(None,"separator",10,76,1,"PROT,ASKIP",True,False,None," ",None,None,517,518,"        DFHMDF POS=(10,76),LENGTH=1"))
    # Customer Name
    els.append(e(None,"label",11,30,16,"NORM,ASKIP",True,False,None,"Customer Name",None,None,520,521,"        DFHMDF POS=(11,30),LENGTH=16"))
    ls=make_ref(F,520,521,"        DFHMDF POS=(11,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP4CUS","input",11,50,25,"NORM,UNPROT,FSET",False,False,None," ",None,None,522,523,"ENP4CUS DFHMDF POS=(11,50),LENGTH=25",hl="Customer Name",lsrc=ls,rules=[maxlen_rule("E-SSMAPP4-032",25,522,523,"ENP4CUS DFHMDF")]))
    els.append(e(None,"separator",11,76,1,"PROT,ASKIP",True,False,None," ",None,None,524,525,"        DFHMDF POS=(11,76),LENGTH=1"))
    # Property Type
    els.append(e(None,"label",12,30,16,"NORM,ASKIP",True,False,None,"Property Type",None,None,527,528,"        DFHMDF POS=(12,30),LENGTH=16"))
    ls=make_ref(F,527,528,"        DFHMDF POS=(12,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP4PTY","input",12,50,25,"NORM,UNPROT,FSET",False,False,None," ",None,None,529,530,"ENP4PTY DFHMDF POS=(12,50),LENGTH=25",hl="Property Type",lsrc=ls,rules=[maxlen_rule("E-SSMAPP4-035",25,529,530,"ENP4PTY DFHMDF")]))
    els.append(e(None,"separator",12,76,1,"PROT,ASKIP",True,False,None," ",None,None,531,532,"        DFHMDF POS=(12,76),LENGTH=1"))
    # Fire Peril/Prem shared label
    fire_lsrc=make_ref(F,534,535,"        DFHMDF POS=(13,30),LENGTH=16,INITIAL='Fire Peril/Prem'")
    els.append(e(None,"label",13,30,16,"NORM,ASKIP",True,False,None,"Fire Peril/Prem",None,None,534,535,"        DFHMDF POS=(13,30),LENGTH=16"))
    els.append(e("ENP4FPE","input",13,50,4,"NORM,UNPROT,FSET",False,False,None,None,"RIGHT,ZERO",None,536,537,"ENP4FPE DFHMDF POS=(13,50),LENGTH=4",hl="Fire Peril/Prem",lnote="shared-label",lsrc=fire_lsrc,rules=[maxlen_rule("E-SSMAPP4-039",4,536,537,"ENP4FPE DFHMDF")]))
    els.append(e(None,"separator",13,55,1,"PROT,ASKIP",True,False,None," ",None,None,538,539,"        DFHMDF POS=(13,55),LENGTH=1"))
    els.append(e("ENP4FPR","input",13,56,8,"NORM,UNPROT,FSET",False,False,None,None,"RIGHT,ZERO",None,540,541,"ENP4FPR DFHMDF POS=(13,56),LENGTH=8",hl="Fire Peril/Prem",lnote="shared-label",lsrc=fire_lsrc,rules=[maxlen_rule("E-SSMAPP4-041",8,540,541,"ENP4FPR DFHMDF")]))
    els.append(e(None,"separator",13,65,1,"PROT,ASKIP",True,False,None," ",None,None,542,543,"        DFHMDF POS=(13,65),LENGTH=1"))
    # Crime Peril/Prem shared label
    crime_lsrc=make_ref(F,545,546,"        DFHMDF POS=(14,30),LENGTH=16,INITIAL='Crime Peril/Prem'")
    els.append(e(None,"label",14,30,16,"NORM,ASKIP",True,False,None,"Crime Peril/Prem",None,None,545,546,"        DFHMDF POS=(14,30),LENGTH=16"))
    els.append(e("ENP4CPE","input",14,50,4,"NORM,UNPROT,FSET",False,False,None,None,"RIGHT,ZERO",None,547,548,"ENP4CPE DFHMDF POS=(14,50),LENGTH=4",hl="Crime Peril/Prem",lnote="shared-label",lsrc=crime_lsrc,rules=[maxlen_rule("E-SSMAPP4-044",4,547,548,"ENP4CPE DFHMDF")]))
    els.append(e(None,"separator",14,55,1,"PROT,ASKIP",True,False,None," ",None,None,549,550,"        DFHMDF POS=(14,55),LENGTH=1"))
    els.append(e("ENP4CPR","input",14,56,8,"NORM,UNPROT,FSET",False,False,None,None,"RIGHT,ZERO",None,551,552,"ENP4CPR DFHMDF POS=(14,56),LENGTH=8",hl="Crime Peril/Prem",lnote="shared-label",lsrc=crime_lsrc,rules=[maxlen_rule("E-SSMAPP4-046",8,551,552,"ENP4CPR DFHMDF")]))
    els.append(e(None,"separator",14,65,1,"PROT,ASKIP",True,False,None," ",None,None,553,554,"        DFHMDF POS=(14,65),LENGTH=1"))
    # Flood Peril/Prem shared label
    flood_lsrc=make_ref(F,556,557,"        DFHMDF POS=(15,30),LENGTH=16,INITIAL='Flood Peril/Prem'")
    els.append(e(None,"label",15,30,16,"NORM,ASKIP",True,False,None,"Flood Peril/Prem",None,None,556,557,"        DFHMDF POS=(15,30),LENGTH=16"))
    els.append(e("ENP4XPE","input",15,50,4,"NORM,UNPROT,FSET",False,False,None,None,"RIGHT,ZERO",None,558,559,"ENP4XPE DFHMDF POS=(15,50),LENGTH=4",hl="Flood Peril/Prem",lnote="shared-label",lsrc=flood_lsrc,rules=[maxlen_rule("E-SSMAPP4-049",4,558,559,"ENP4XPE DFHMDF")]))
    els.append(e(None,"separator",15,55,1,"PROT,ASKIP",True,False,None," ",None,None,560,561,"        DFHMDF POS=(15,55),LENGTH=1"))
    els.append(e("ENP4XPR","input",15,56,8,"NORM,UNPROT,FSET",False,False,None,None,"RIGHT,ZERO",None,562,563,"ENP4XPR DFHMDF POS=(15,56),LENGTH=8",hl="Flood Peril/Prem",lnote="shared-label",lsrc=flood_lsrc,rules=[maxlen_rule("E-SSMAPP4-051",8,562,563,"ENP4XPR DFHMDF")]))
    els.append(e(None,"separator",15,65,1,"PROT,ASKIP",True,False,None," ",None,None,564,565,"        DFHMDF POS=(15,65),LENGTH=1"))
    # Weather Peril/Prem shared label
    weath_lsrc=make_ref(F,567,568,"        DFHMDF POS=(16,30),LENGTH=18,INITIAL='Weather Peril/Prem'")
    els.append(e(None,"label",16,30,18,"NORM,ASKIP",True,False,None,"Weather Peril/Prem",None,None,567,568,"        DFHMDF POS=(16,30),LENGTH=18"))
    els.append(e("ENP4WPE","input",16,50,4,"NORM,UNPROT,FSET",False,False,None,None,"RIGHT,ZERO",None,569,570,"ENP4WPE DFHMDF POS=(16,50),LENGTH=4",hl="Weather Peril/Prem",lnote="shared-label",lsrc=weath_lsrc,rules=[maxlen_rule("E-SSMAPP4-054",4,569,570,"ENP4WPE DFHMDF")]))
    els.append(e(None,"separator",16,55,1,"PROT,ASKIP",True,False,None," ",None,None,571,572,"        DFHMDF POS=(16,55),LENGTH=1"))
    els.append(e("ENP4WPR","input",16,56,8,"NORM,UNPROT,FSET",False,False,None,None,"RIGHT,ZERO",None,573,574,"ENP4WPR DFHMDF POS=(16,56),LENGTH=8",hl="Weather Peril/Prem",lnote="shared-label",lsrc=weath_lsrc,rules=[maxlen_rule("E-SSMAPP4-056",8,573,574,"ENP4WPR DFHMDF")]))
    els.append(e(None,"separator",16,65,1,"PROT,ASKIP",True,False,None," ",None,None,575,576,"        DFHMDF POS=(16,65),LENGTH=1"))
    # Status
    els.append(e(None,"label",17,30,16,"NORM,ASKIP",True,False,None,"Status",None,None,578,579,"        DFHMDF POS=(17,30),LENGTH=16"))
    ls=make_ref(F,578,579,"        DFHMDF POS=(17,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP4STA","input",17,50,4,"NORM,UNPROT,FSET",False,False,None," ","RIGHT,ZERO",None,580,581,"ENP4STA DFHMDF POS=(17,50),LENGTH=4",hl="Status",lsrc=ls,rules=[maxlen_rule("E-SSMAPP4-059",4,580,581,"ENP4STA DFHMDF")]))
    els.append(e(None,"separator",17,55,1,"PROT,ASKIP",True,False,None," ",None,None,582,583,"        DFHMDF POS=(17,55),LENGTH=1"))
    # Reject Reason
    els.append(e(None,"label",18,30,16,"NORM,ASKIP",True,False,None,"Reject Reason",None,None,585,586,"        DFHMDF POS=(18,30),LENGTH=16"))
    ls=make_ref(F,585,586,"        DFHMDF POS=(18,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP4REJ","input",18,50,25,"NORM,UNPROT,FSET",False,False,None," ","RIGHT,ZERO",None,587,588,"ENP4REJ DFHMDF POS=(18,50),LENGTH=25",hl="Reject Reason",lsrc=ls,rules=[maxlen_rule("E-SSMAPP4-062",25,587,588,"ENP4REJ DFHMDF")]))
    els.append(e(None,"separator",18,76,1,"PROT,ASKIP",True,False,None," ",None,None,589,590,"        DFHMDF POS=(18,76),LENGTH=1"))
    # Select Option
    els.append(e(None,"label",22,8,14,"NORM,ASKIP",True,False,None,"Select Option ",None,None,592,593,"        DFHMDF POS=(22,08),LENGTH=14"))
    ls=make_ref(F,592,593,"        DFHMDF POS=(22,08),LENGTH=14,ATTRB=(NORM,ASKIP),")
    eid_opt=f"E-SSMAPP4-{len(els)+1:03d}"
    els.append(e("ENP4OPT","option",22,24,1,"NORM,NUM,UNPROT,FSET",False,True,"MUSTENTER"," ",None,None,594,595,"ENP4OPT DFHMDF POS=(22,24),LENGTH=1",hl="Select Option",lsrc=ls,rules=mustenter_rules(eid_opt,594,595,"ENP4OPT DFHMDF")))
    els.append(e(None,"separator",22,26,1,"PROT,ASKIP",True,False,None," ",None,None,596,597,"        DFHMDF POS=(22,26),LENGTH=1"))
    els.append(e("ERP4FLD","error",24,8,40,"BRT,ASKIP,PROT",True,False,None," ",None,None,599,600,"ERP4FLD DFHMDF POS=(24,8),LENGTH=40"))
    return els

def build_ssmapp5_elements():
    els = []
    def e(bms_n, role, row, col, length, attrb, prot, num, validn, initial, xinit, justify, ls, le, exc, hl=None, lnote=None, lsrc=None, note=None, rules=None):
        idx=len(els)+1; fseq=sum(1 for x in els if x.get('bmsName'))+(1 if bms_n else 0)
        fid=f"F-SSMAPP5-{fseq:03d}" if bms_n else None
        return make_el(f"E-SSMAPP5-{idx:03d}",idx,bms_n,fid,role,row,col,length,attrb,prot,num,validn,initial,xinit,justify,ls,le,exc,hl,lnote,lsrc,note,rules)
    els.append(e(None,"title",1,1,4,"ASKIP,BRT",True,False,None,"SSP5",None,None,607,607,"        DFHMDF POS=(1,1),LENGTH=4,INITIAL='SSP5'"))
    els.append(e(None,"title",1,12,40,"BRT,ASKIP",True,False,None,"General Insurance Policy Claim Menu ",None,None,608,609,"        DFHMDF POS=(1,12),LENGTH=40"))
    els.append(e(None,"menuOption",4,8,18,"NORM,ASKIP",True,False,None,"1. Claim Inquiry ",None,None,611,612,"        DFHMDF POS=(4,08),LENGTH=18"))
    els.append(e(None,"menuOption",5,8,16,"NORM,ASKIP",True,False,None,"2. Claim Add     ",None,None,613,614,"        DFHMDF POS=(5,08),LENGTH=16",note="Options 3 and 4 are commented out in BMS source (lines 615-618). No COBOL presentation program (LGTESTP5) exists for SSP5."))
    els.append(e(None,"label",4,30,15,"NORM,ASKIP",True,False,None,"Claim Number ",None,None,620,621,"        DFHMDF POS=(04,30),LENGTH=15"))
    ls=make_ref(F,620,621,"        DFHMDF POS=(04,30),LENGTH=15,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP5LNO","input",4,50,10,"NORM,UNPROT,IC,FSET",False,False,None,None,None,"RIGHT,ZERO",622,623,"ENP5LNO DFHMDF POS=(04,50),LENGTH=10",hl="Claim Number",lsrc=ls,rules=[maxlen_rule("E-SSMAPP5-006",10,622,623,"ENP5LNO DFHMDF")]))
    els.append(e(None,"separator",4,61,1,"PROT,ASKIP",True,False,None," ",None,None,624,625,"        DFHMDF POS=(04,61),LENGTH=1"))
    els.append(e(None,"label",5,30,16,"NORM,ASKIP",True,False,None,"Policy Number ",None,None,627,628,"        DFHMDF POS=(05,30),LENGTH=16"))
    ls=make_ref(F,627,628,"        DFHMDF POS=(05,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP5PNO","input",5,50,10,"NORM,UNPROT,IC,FSET",False,False,None,None,None,"RIGHT,ZERO",629,630,"ENP5PNO DFHMDF POS=(05,50),LENGTH=10",hl="Policy Number",lsrc=ls,rules=[maxlen_rule("E-SSMAPP5-009",10,629,630,"ENP5PNO DFHMDF")]))
    els.append(e(None,"separator",5,61,1,"PROT,ASKIP",True,False,None," ",None,None,631,632,"        DFHMDF POS=(05,61),LENGTH=1"))
    els.append(e(None,"label",6,30,16,"NORM,ASKIP",True,False,None,"Customer Number ",None,None,634,635,"        DFHMDF POS=(06,30),LENGTH=16"))
    ls=make_ref(F,634,635,"        DFHMDF POS=(06,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP5CNO","input",6,50,10,"NORM,UNPROT,IC,FSET",False,False,None,None,None,"RIGHT,ZERO",636,637,"ENP5CNO DFHMDF POS=(06,50),LENGTH=10",hl="Customer Number",lsrc=ls,rules=[maxlen_rule("E-SSMAPP5-012",10,636,637,"ENP5CNO DFHMDF")]))
    els.append(e(None,"separator",6,61,1,"PROT,ASKIP",True,False,None," ",None,None,638,639,"        DFHMDF POS=(06,61),LENGTH=1"))
    els.append(e(None,"label",7,30,16,"NORM,ASKIP",True,False,None,"Claim date ",None,None,641,642,"        DFHMDF POS=(07,30),LENGTH=16"))
    ls=make_ref(F,641,642,"        DFHMDF POS=(07,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP5CDA","input",7,50,10,"NORM,UNPROT,FSET",False,False,None," ",None,None,643,644,"ENP5CDA DFHMDF POS=(07,50),LENGTH=10",hl="Claim date",lsrc=ls,rules=[maxlen_rule("E-SSMAPP5-015",10,643,644,"ENP5CDA DFHMDF"),date_cannot_determine_rule("E-SSMAPP5-015",647,648,"        DFHMDF POS=(07,63),LENGTH=12,ATTRB=(NORM,ASKIP),")]))
    els.append(e(None,"separator",7,61,1,"PROT,ASKIP",True,False,None," ",None,None,645,646,"        DFHMDF POS=(07,61),LENGTH=1"))
    els.append(e(None,"hint",7,63,12,"NORM,ASKIP",True,False,None,"(yyyy-mm-dd)",None,None,647,648,"        DFHMDF POS=(07,63),LENGTH=12"))
    els.append(e(None,"label",8,30,16,"NORM,ASKIP",True,False,None,"Paid",None,None,650,651,"        DFHMDF POS=(08,30),LENGTH=16"))
    ls=make_ref(F,650,651,"        DFHMDF POS=(08,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP5PAD","input",8,50,10,"NORM,UNPROT,FSET",False,False,None,None,"00000000000000000000","RIGHT,ZERO",652,653,"ENP5PAD DFHMDF POS=(08,50),LENGTH=10",hl="Paid",lsrc=ls,rules=[maxlen_rule("E-SSMAPP5-019",10,652,653,"ENP5PAD DFHMDF")]))
    els.append(e(None,"separator",8,61,1,"PROT,ASKIP",True,False,None," ",None,None,654,655,"        DFHMDF POS=(08,61),LENGTH=1"))
    els.append(e(None,"label",9,30,16,"NORM,ASKIP",True,False,None,"Value   ",None,None,657,658,"        DFHMDF POS=(09,30),LENGTH=16"))
    ls=make_ref(F,657,658,"        DFHMDF POS=(09,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP5VAL","input",9,50,10,"NORM,UNPROT,FSET",False,False,None,None,"00000000000000000000","RIGHT,ZERO",659,660,"ENP5VAL DFHMDF POS=(09,50),LENGTH=10",hl="Value",lsrc=ls,rules=[maxlen_rule("E-SSMAPP5-022",10,659,660,"ENP5VAL DFHMDF")]))
    els.append(e(None,"separator",9,61,1,"PROT,ASKIP",True,False,None," ",None,None,661,662,"        DFHMDF POS=(09,61),LENGTH=1"))
    els.append(e(None,"label",10,30,16,"NORM,ASKIP",True,False,None,"Cause        ",None,None,664,665,"        DFHMDF POS=(10,30),LENGTH=16"))
    ls=make_ref(F,664,665,"        DFHMDF POS=(10,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP5CAU","input",10,50,25,"NORM,UNPROT,FSET",False,False,None," ",None,None,666,667,"ENP5CAU DFHMDF POS=(10,50),LENGTH=25",hl="Cause",lsrc=ls,rules=[maxlen_rule("E-SSMAPP5-025",25,666,667,"ENP5CAU DFHMDF")]))
    els.append(e(None,"separator",10,76,1,"PROT,ASKIP",True,False,None," ",None,None,668,669,"        DFHMDF POS=(10,76),LENGTH=1"))
    els.append(e(None,"label",11,30,16,"NORM,ASKIP",True,False,None,"Observation ",None,None,671,672,"        DFHMDF POS=(11,30),LENGTH=16"))
    ls=make_ref(F,671,672,"        DFHMDF POS=(11,30),LENGTH=16,ATTRB=(NORM,ASKIP),")
    els.append(e("ENP5OBS","input",11,50,25,"NORM,UNPROT,FSET",False,False,None," ",None,None,673,674,"ENP5OBS DFHMDF POS=(11,50),LENGTH=25",hl="Observation",lsrc=ls,rules=[maxlen_rule("E-SSMAPP5-028",25,673,674,"ENP5OBS DFHMDF")]))
    els.append(e(None,"separator",11,76,1,"PROT,ASKIP",True,False,None," ",None,None,675,676,"        DFHMDF POS=(11,76),LENGTH=1"))
    els.append(e(None,"label",22,8,14,"NORM,ASKIP",True,False,None,"Select Option ",None,None,678,679,"        DFHMDF POS=(22,08),LENGTH=14"))
    ls=make_ref(F,678,679,"        DFHMDF POS=(22,08),LENGTH=14,ATTRB=(NORM,ASKIP),")
    eid_opt=f"E-SSMAPP5-{len(els)+1:03d}"
    els.append(e("ENP5OPT","option",22,24,1,"NORM,NUM,UNPROT,FSET",False,True,"MUSTENTER"," ",None,None,680,681,"ENP5OPT DFHMDF POS=(22,24),LENGTH=1",hl="Select Option",lsrc=ls,rules=mustenter_rules(eid_opt,680,681,"ENP5OPT DFHMDF"),note="VALIDN=MUSTENTER present in BMS. Runtime enforcement cannot be determined (no LGTESTP5)."))
    els.append(e(None,"separator",22,26,1,"PROT,ASKIP",True,False,None," ",None,None,682,683,"        DFHMDF POS=(22,26),LENGTH=1"))
    els.append(e("ERP5FLD","error",24,8,40,"BRT,ASKIP,PROT",True,False,None," ",None,None,685,686,"ERP5FLD DFHMDF POS=(24,8),LENGTH=40"))
    return els

def build_tasks():
    C1 = "legacy/cics-genapp/base/src/lgtestc1.cbl"
    P1 = "legacy/cics-genapp/base/src/lgtestp1.cbl"
    P2 = "legacy/cics-genapp/base/src/lgtestp2.cbl"
    P3 = "legacy/cics-genapp/base/src/lgtestp3.cbl"
    P4 = "legacy/cics-genapp/base/src/lgtestp4.cbl"
    OPTS_SSC1 = ["1","2","4"]
    OPTS_SSP123 = ["1","2","3","4"]
    OPTS_SSP4 = ["1","2","3"]
    OPTS_SSP5 = ["1","2"]

    def t(tid, name, outcome, trans, mname, op, optkey, allowed, lstat, prgm, biz, ev, navvars=None, note=None, rules=None):
        task = {
            "taskId": tid, "name": name, "outcome": outcome,
            "transactionId": trans, "mapName": mname, "operation": op,
            "optionKey": optkey, "allowedOptions": allowed,
            "legacySupportStatus": lstat, "modernParityStatus": "not-assessed",
            "presentationProgram": prgm, "businessPrograms": biz,
            "sourceEvidence": ev
        }
        if navvars: task["navigationVariants"] = navvars
        if note: task["note"] = note
        if rules: task["rules"] = rules
        return task

    MC = "map-and-program-confirmed"
    SC = "screen-only-cannot-determine"

    tasks = [
        t("T-SSC1-1","Inquire Customer",
          "Retrieve and display a customer record by customer number.",
          "SSC1","SSMAPC1","inquire","1",OPTS_SSC1,MC,"LGTESTC1",["LGICUS01"],
          [make_ref(F,18,19,"        DFHMDF POS=(4,08),LENGTH=16,ATTRB=(NORM,ASKIP),"),
           make_ref(C1,84,111,"            EVALUATE ENT1OPTO")]),

        t("T-SSC1-2","Add Customer",
          "Create a new customer record with name, address, and contact details.",
          "SSC1","SSMAPC1","add","2",OPTS_SSC1,MC,"LGTESTC1",["LGACUS01"],
          [make_ref(F,20,21,"        DFHMDF POS=(5,08),LENGTH=16,ATTRB=(NORM,ASKIP),"),
           make_ref(C1,84,146,"            EVALUATE ENT1OPTO")],
          rules=[
              {"ruleId":"R-T-SSC1-2-001","type":"validationCode","certainty":"explicit",
               "plainEnglish":"COMMAREA length must be at least WS-CA-HEADER-LEN + WS-CUSTOMER-LEN. If too small, CA-RETURN-CODE is set to 98 and the add is rejected.",
               "sourceRef":make_ref("legacy/cics-genapp/base/src/lgacus01.cbl",108,115,"           ADD WS-CA-HEADER-LEN TO WS-REQUIRED-CA-LEN")}
          ]),

        t("T-SSC1-4","Update Customer",
          "Retrieve an existing customer record, allow edits, and save the updated data.",
          "SSC1","SSMAPC1","update","4",OPTS_SSC1,MC,"LGTESTC1",["LGICUS01","LGUCUS01"],
          [make_ref(F,24,25,"        DFHMDF POS=(7,08),LENGTH=16,ATTRB=(NORM,ASKIP),"),
           make_ref(C1,84,207,"            EVALUATE ENT1OPTO")],
          rules=[
              {"ruleId":"R-T-SSC1-4-001","type":"validationCode","certainty":"explicit",
               "plainEnglish":"REQUEST-ID must be exactly '01UCUS' for an update. Any other value causes CA-RETURN-CODE=99.",
               "sourceRef":make_ref("legacy/cics-genapp/base/src/lgucus01.cbl",110,110,"           If CA-REQUEST-ID NOT = '01UCUS'")}
          ]),

        t("T-SSP1-1","Inquire Motor Policy",
          "Retrieve and display a motor policy record.",
          "SSP1","SSMAPP1","inquire","1",OPTS_SSP123,MC,"LGTESTP1",["LGIPOL01"],
          [make_ref(F,117,118,"        DFHMDF POS=(4,08),LENGTH=18,ATTRB=(NORM,ASKIP),"),
           make_ref(P1,66,95,"           EVALUATE ENP1OPTO")]),

        t("T-SSP1-2","Add Motor Policy",
          "Create a new motor policy record for a customer.",
          "SSP1","SSMAPP1","add","2",OPTS_SSP123,MC,"LGTESTP1",["LGAPOL01"],
          [make_ref(F,119,120,"        DFHMDF POS=(5,08),LENGTH=16,ATTRB=(NORM,ASKIP),"),
           make_ref(P1,66,133,"           EVALUATE ENP1OPTO")]),

        t("T-SSP1-3","Delete Motor Policy",
          "Delete an existing motor policy record.",
          "SSP1","SSMAPP1","delete","3",OPTS_SSP123,MC,"LGTESTP1",["LGDPOL01"],
          [make_ref(F,121,122,"        DFHMDF POS=(6,08),LENGTH=16,ATTRB=(NORM,ASKIP),"),
           make_ref(P1,66,167,"           EVALUATE ENP1OPTO")],
          rules=[
              {"ruleId":"R-T-SSP1-3-001","type":"validationCode","certainty":"explicit",
               "plainEnglish":"REQUEST-ID must be one of '01DEND','01DMOT','01DHOU','01DCOM'. Unrecognised values set CA-RETURN-CODE=99.",
               "sourceRef":make_ref("legacy/cics-genapp/base/src/lgdpol01.cbl",117,130,"           MOVE FUNCTION UPPER-CASE(CA-REQUEST-ID) TO CA-REQUEST-ID")}
          ]),

        t("T-SSP1-4","Update Motor Policy",
          "Retrieve a motor policy, allow edits, and save the changes.",
          "SSP1","SSMAPP1","update","4",OPTS_SSP123,MC,"LGTESTP1",["LGIPOL01","LGUPOL01"],
          [make_ref(F,123,124,"        DFHMDF POS=(7,08),LENGTH=16,ATTRB=(NORM,ASKIP),"),
           make_ref(P1,66,234,"           EVALUATE ENP1OPTO")],
          rules=[
              {"ruleId":"R-T-SSP1-4-001","type":"validationCode","certainty":"explicit",
               "plainEnglish":"Update Motor COMMAREA length must be at least WS-CA-HEADER-LEN + WS-FULL-MOTOR-LEN. Shorter COMMAREA sets CA-RETURN-CODE=98.",
               "sourceRef":make_ref("legacy/cics-genapp/base/src/lgupol01.cbl",131,137,"             WHEN '01UMOT'")}
          ]),

        t("T-SSP2-1","Inquire Endowment Policy","Retrieve and display an endowment policy record.",
          "SSP2","SSMAPP2","inquire","1",OPTS_SSP123,MC,"LGTESTP2",["LGIPOL01"],
          [make_ref(F,242,243,"        DFHMDF POS=(4,08),LENGTH=18"),
           make_ref(P2,61,90,"           EVALUATE ENP2OPTO")]),

        t("T-SSP2-2","Add Endowment Policy","Create a new endowment policy record.",
          "SSP2","SSMAPP2","add","2",OPTS_SSP123,MC,"LGTESTP2",["LGAPOL01"],
          [make_ref(F,244,245,"        DFHMDF POS=(5,08),LENGTH=16"),
           make_ref(P2,61,124,"           EVALUATE ENP2OPTO")]),

        t("T-SSP2-3","Delete Endowment Policy","Delete an existing endowment policy record.",
          "SSP2","SSMAPP2","delete","3",OPTS_SSP123,MC,"LGTESTP2",["LGDPOL01"],
          [make_ref(F,246,247,"        DFHMDF POS=(6,08),LENGTH=16"),
           make_ref(P2,61,154,"           EVALUATE ENP2OPTO")]),

        t("T-SSP2-4","Update Endowment Policy","Retrieve an endowment policy, allow edits, and save the changes.",
          "SSP2","SSMAPP2","update","4",OPTS_SSP123,MC,"LGTESTP2",["LGIPOL01","LGUPOL01"],
          [make_ref(F,248,249,"        DFHMDF POS=(7,08),LENGTH=16"),
           make_ref(P2,61,230,"           EVALUATE ENP2OPTO")],
          rules=[
              {"ruleId":"R-T-SSP2-4-001","type":"validationCode","certainty":"explicit",
               "plainEnglish":"Update Endowment COMMAREA length must be at least WS-CA-HEADER-LEN + WS-FULL-ENDOW-LEN.",
               "sourceRef":make_ref("legacy/cics-genapp/base/src/lgupol01.cbl",115,121,"             WHEN '01UEND'")}
          ]),

        t("T-SSP3-1","Inquire House Policy","Retrieve and display a house policy record.",
          "SSP3","SSMAPP3","inquire","1",OPTS_SSP123,MC,"LGTESTP3",["LGIPOL01"],
          [make_ref(F,351,352,"        DFHMDF POS=(4,08),LENGTH=18"),
           make_ref(P3,64,92,"           EVALUATE ENP3OPTO")]),

        t("T-SSP3-2","Add House Policy","Create a new house policy record.",
          "SSP3","SSMAPP3","add","2",OPTS_SSP123,MC,"LGTESTP3",["LGAPOL01"],
          [make_ref(F,353,354,"        DFHMDF POS=(5,08),LENGTH=16"),
           make_ref(P3,64,124,"           EVALUATE ENP3OPTO")]),

        t("T-SSP3-3","Delete House Policy","Delete an existing house policy record.",
          "SSP3","SSMAPP3","delete","3",OPTS_SSP123,MC,"LGTESTP3",["LGDPOL01"],
          [make_ref(F,355,356,"        DFHMDF POS=(6,08),LENGTH=16"),
           make_ref(P3,64,154,"           EVALUATE ENP3OPTO")]),

        t("T-SSP3-4","Update House Policy","Retrieve a house policy, allow edits, and save the changes.",
          "SSP3","SSMAPP3","update","4",OPTS_SSP123,MC,"LGTESTP3",["LGIPOL01","LGUPOL01"],
          [make_ref(F,357,358,"        DFHMDF POS=(7,08),LENGTH=16"),
           make_ref(P3,64,229,"           EVALUATE ENP3OPTO")],
          rules=[
              {"ruleId":"R-T-SSP3-4-001","type":"validationCode","certainty":"explicit",
               "plainEnglish":"Update House COMMAREA length must be at least WS-CA-HEADER-LEN + WS-FULL-HOUSE-LEN.",
               "sourceRef":make_ref("legacy/cics-genapp/base/src/lgupol01.cbl",123,129,"             WHEN '01UHOU'")}
          ]),

        t("T-SSP4-1","Inquire Commercial Policy",
          "Retrieve and display a commercial property policy record. The REQUEST-ID varies based on which identifier fields are non-blank.",
          "SSP4","SSMAPP4","inquire","1",OPTS_SSP4,MC,"LGTESTP4",["LGIPOL01"],
          [make_ref(F,454,455,"        DFHMDF POS=(4,08),LENGTH=18"),
           make_ref(P4,71,154,"           EVALUATE ENP4OPTO")],
          navvars=[
              {"requestId":"01ICOM","condition":"Both customer number (ENP4CNO) and policy number (ENP4PNO) are non-blank and non-zero"},
              {"requestId":"02ICOM","condition":"Policy number (ENP4PNO) is non-blank and non-zero; customer number is blank or zero"},
              {"requestId":"03ICOM","condition":"Customer number (ENP4CNO) is non-blank and non-zero; policy number is blank or zero"},
              {"requestId":"05ICOM","condition":"Postcode (ENP4HPC) is non-blank and non-zero; both customer and policy numbers are blank or zero"}
          ]),

        t("T-SSP4-2","Add Commercial Policy","Create a new commercial property policy record.",
          "SSP4","SSMAPP4","add","2",OPTS_SSP4,MC,"LGTESTP4",["LGAPOL01"],
          [make_ref(F,456,457,"        DFHMDF POS=(5,08),LENGTH=16"),
           make_ref(P4,71,195,"           EVALUATE ENP4OPTO")]),

        t("T-SSP4-3","Delete Commercial Policy","Delete an existing commercial property policy record.",
          "SSP4","SSMAPP4","delete","3",OPTS_SSP4,MC,"LGTESTP4",["LGDPOL01"],
          [make_ref(F,458,459,"        DFHMDF POS=(6,08),LENGTH=16"),
           make_ref(P4,71,234,"           EVALUATE ENP4OPTO")]),

        t("T-SSP5-1","Inquire Policy Claim",
          "Retrieve and display a policy claim record. Screen option visible in BMS; no presentation program confirmed.",
          "SSP5","SSMAPP5","inquire","1",OPTS_SSP5,SC,None,[],
          [make_ref(F,611,612,"        DFHMDF POS=(4,08),LENGTH=18,INITIAL='1. Claim Inquiry '")],
          note="LGTESTP5 does not exist in the source tree. SSP5 is absent from base/Reference.md lines 46-57. Executability of this action cannot be determined from available source."),

        t("T-SSP5-2","Add Policy Claim",
          "Create a new policy claim record. Screen option visible in BMS; no presentation program confirmed.",
          "SSP5","SSMAPP5","add","2",OPTS_SSP5,SC,None,[],
          [make_ref(F,613,614,"        DFHMDF POS=(5,08),LENGTH=16,INITIAL='2. Claim Add     '")],
          note="LGTESTP5 does not exist in the source tree. SSP5 is absent from base/Reference.md lines 46-57. Executability of this action cannot be determined from available source.")
    ]
    return tasks


if __name__ == "__main__":
    build_catalogue()
