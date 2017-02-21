from cbverifier.specs.spec import Spec
import argparse

def cycle_lines(in_file, out_file):
    with open(in_file, 'r') as f:
        for line in f:
            if len(line) > 0 and line[0] != '/':
                trimedLine = line.split(";")[0]
                parsedspec = Spec.get_spec_from_string(trimedLine)
                print parsedspec

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Print human readable data from protobuf trace')
    parser.add_argument('--input', type=str,
                        help="input file",required=True)
    parser.add_argument('--output', type=str,
                        help="input file",required=True)
    args = parser.parse_args()

    cycle_lines(args.input, args.output)