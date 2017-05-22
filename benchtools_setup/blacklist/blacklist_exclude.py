import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sort trace by message ID')
    parser.add_argument('--excl', type=str,
                        help="exclusion files separated by colon",required=True)
    parser.add_argument('--dir', type=str,
                        help="instances directory of *.txt files to remove bad apps from")

    args = parser.parse_args()

    exclusions = []
    for f in args.excl.split(":"):
        cf = open(f,'r')
        cexclusions = cf.readlines()

        for exclusion in cexclusions:
            exclusions.append(exclusion)
    pass
