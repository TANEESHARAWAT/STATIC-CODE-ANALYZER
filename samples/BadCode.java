// Sample Java file with intentional rule violations for testing

public class badClass {              // JV001: not PascalCase

    public void MyMethod() {         // JV002: not camelCase
        System.out.println("debug"); // JV005: debug print left in

        try {
            int x = 10 / 0;
        } catch (Exception e) {
            // JV003: empty catch block — exception silently ignored
        }
    }

    public void goodMethod() {
        try {
            int result = 10 / 2;
            System.err.println("Result: " + result);
        } catch (ArithmeticException e) {
            System.err.println("Error: " + e.getMessage());
        }
    }
}
