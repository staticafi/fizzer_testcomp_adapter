#!/bin/bash

SELF=$(dirname "$(realpath "$0")")
DIR="/tmp/TestCompSmokeTest_fizzer"
FILE="$DIR/a.c"
PRP="$DIR/b.prp"

mkdir -p "$DIR"

cat > "$FILE" << 'EOF'
extern char __VERIFIER_nondet_char();

int main()
{
    char  data[4];
    data[0] = __VERIFIER_nondet_char();
    data[1] = __VERIFIER_nondet_char();
    data[2] = __VERIFIER_nondet_char();
    data[3] = __VERIFIER_nondet_char();

    if (data[0] == 'b')
        if (data[1] == 'a')
            if (data[2] == 'd')
                if (data[3] == '!')
                    return 1;
    return 0;
}
EOF
echo "C file created at: $FILE"

cat > "$PRP" << 'EOF'
COVER( init(main()), FQL(COVER EDGES(@DECISIONEDGE)) )
EOF
echo "PRP file created at: $PRP"

echo "Results will be written to: $DIR"

cd "$DIR"
python3 "$SELF/sbt-fizzer.py" --input_file "$FILE" --property "$PRP"
