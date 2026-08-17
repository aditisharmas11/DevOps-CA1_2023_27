# Java

Compile and run from inside this folder (or from the repo root):

```bash
cd java
javac Luhn.java
java Luhn
```

The program tries `test_numbers.txt` first, then falls back to `../test_numbers.txt` when run from inside `java/`, so it works from both locations.
