import java.util.*;

public class A_Cover_in_Water {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int t = sc.nextInt();

        while (t-- > 0) {
            int n = sc.nextInt();
            String s = sc.next();

            int totalDots = 0;
            boolean hasBigSegment = false;

            int i = 0;
            while (i < n) {
                if (s.charAt(i) == '.') {
                    int j = i;

                    while (j < n && s.charAt(j) == '.') {
                        j++;
                    }

                    int len = j - i;
                    totalDots += len;

                    if (len >= 3) {
                        hasBigSegment = true;
                    }

                    i = j;
                } else {
                    i++;
                }
            }

            if (hasBigSegment) {
                System.out.println(2);
            } else {
                System.out.println(totalDots);
            }
        }

        sc.close();
    }
}