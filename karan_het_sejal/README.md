# CA-1 Task 3 Submission: Open Source Contribution on Rex-Socket

## Group Information
- **Group Members:** Karan Desai, Het Jasani, Sejal More, Dakshit Singh

## Target Repository
- **Repository:** [rapid7/rex-socket](https://github.com/rapid7/rex-socket)

## Target Issue
- **Issue:** [rapid7/metasploit-framework#21113](https://github.com/rapid7/metasploit-framework/issues/21113)

## Pull Request
- **PR Link:** [rapid7/rex-socket#80](https://github.com/rapid7/rex-socket/pull/80)

## Contribution Summary
This open-source contribution added support for an `Interface` socket option in `Rex::Socket::Parameters`, allowing callers to bind sockets to a specific network interface by name.

The feature was useful for broadcast-capable sockets, where binding by IP address alone was not enough. It enabled Metasploit/Rex socket users to choose a network interface directly.

## What Was Done
- Added an `Interface` option to `Rex::Socket::Parameters`
- Updated socket binding logic in `lib/rex/socket/comm/local.rb`
- Added platform-aware handling for Linux, macOS, and Windows
- Added safeguards for invalid interface names and proxy conflicts
- Added and updated RSpec tests for the new behavior
- Fixed interface binding order so socket options are applied before `bind()` for correct kernel behavior
- Reworked platform handling and error messages based on maintainer review
- Verified the implementation with testing on Linux and macOS

## Merge Status
- **Status:** Merged successfully
- **Merged Into:** `rapid7:master`
- **Checks Passed:** 21

## Evidence
- Branch: `karandesai2005:feature/interface-param-21114`
- Final PR status: merged
- Review feedback was addressed through multiple updates before merge
- <img width="1806" height="943" alt="image" src="https://github.com/user-attachments/assets/7aa1925f-7b93-4236-8960-1965f71e0ef2" />
<img width="1839" height="982" alt="image" src="https://github.com/user-attachments/assets/e6eb060d-bad5-4b54-9735-3b9ef9cad49a" />



## Notes
This submission documents a real upstream open-source contribution that was merged after review and testing.
