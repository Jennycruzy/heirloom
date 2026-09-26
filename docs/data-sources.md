# Data Sources

## IBM CICS GenApp

| Item | Value |
|------|-------|
| Repository | https://github.com/cicsdev/cics-genapp |
| Pinned commit (gitlink) | `f6f3f4b2580d31b7d8dcc31ce3e3676f4cceaaaa` |
| Local path | `legacy/cics-genapp` |

### Licence

IBM CICS GenApp is licensed under the **Eclipse Public License 2.0 (EPL-2.0)**.  
See: <https://www.eclipse.org/legal/epl-2.0/>  
The upstream licence file is included in the submodule at `legacy/cics-genapp/LICENSE`.

IBM Corporation is the copyright holder of the GenApp source. IBM does not endorse Heirloom.

### Sample data

The customer, policy, and commercial records included in the GenApp source are IBM fictional sample data. They do not represent real persons, businesses, or financial records and must not be treated as such.

### How Heirloom uses this source

Heirloom reads GenApp COBOL and SSMAP source files to determine what fields, rules, and behaviours the original green-screen application defined. Heirloom does not run a mainframe, does not execute GenApp, and does not require a CICS environment.
