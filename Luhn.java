import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Luhn checksum implementation and test runner.
 *
 * Path convention: this program expects to be run from the repository root so
 * it can read "test_numbers.txt" from the project root:
 *   javac java/Luhn.java
 *   java -cp . java.Luhn
 *
 * The program reads test_numbers.txt, parses lines of the form
 *   <label>| <number>,<expected>
 * and prints a PASS/FAIL for each case.
 *
 * Only uses the Java standard library.
 */
public class Luhn {

    public static boolean luhnCheck(String input) {
        // Extract digits and reverse order
        List<Integer> digits = new ArrayList<>();
        for (int i = input.length() - 1; i >= 0; i--) {
            char c = input.charAt(i);
            if (Character.isDigit(c)) {
                digits.add(c - '0');
            }
        }

        int total = 0;
        for (int i = 0; i < digits.size(); i++) {
            int d = digits.get(i);
            if (i % 2 == 1) {
                d *= 2;
                if (d > 9) d -= 9;
            }
            total += d;
        }
        return total % 10 == 0;
    }

    public static void main(String[] args) {
        Path testFile = Paths.get(System.getProperty("user.dir"), "test_numbers.txt");
        try {
            List<String> lines = Files.readAllLines(testFile);
            for (String raw : lines) {
                if (raw == null) continue;
                String line = raw.trim();
                if (line.isEmpty()) continue;

                // Expecting a comma separating number and expected label
                String[] parts = line.split(",", 2);
                if (parts.length < 2) {
                    // Skip malformed lines
                    System.out.println(line + " -> SKIPPED (malformed)");
                    continue;
                }

                String number = parts[0].trim();
                String expected = parts[1].trim();

                boolean ok = luhnCheck(number);
                String result = ok ? "valid" : "invalid";
                String status = result.equals(expected) ? "PASS" : "FAIL";
                System.out.printf("%s -> %s (expected: %s) [%s]%n", number, result, expected, status);
            }
        } catch (IOException e) {
            System.err.println("Failed to read test_numbers.txt: " + e.getMessage());
            e.printStackTrace();
            System.exit(2);
        }
    }
}
