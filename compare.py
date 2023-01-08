import ast
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('indir', type=str, default='input.txt')
parser.add_argument('outdir', type=str, default='scores.txt')
args = parser.parse_args()


def to_ast(filename: str) -> str:
    """
    Convert code to ast code

    :param filename:
    :return text of code as string:
    """
    with open(filename, 'r') as f:
        text = f.read()
    tree_ast = ast.parse(text)
    tree_str = str(ast.dump(tree_ast))
    return tree_str


def cleaning(filename: str) -> list:
    """
    Separate text

    :param filename:
    :return list of modules:
    """
    text = to_ast(filename)
    modules = text.split(',')
    modules = [module.strip() for module in modules]
    return modules


def antiplagiat(str1: str, str2: str) -> float:
    """
    Comparing texts using Levenshtein distance

    :param str1:
    :param str2:
    :return coefficient of comparing texts:
    """
    a = len(str1) + 1
    b = len(str2) + 1
    matrix = [[i + j if i * j == 0 else 0 for j in range(b)] for i in range(a)]
    for i in range(1, a):
        for j in range(1, b):
            if str1[i - 1] == str2[j - 1]:
                matrix[i][j] = matrix[i - 1][j - 1]
            else:
                matrix[i][j] = 1 + min(matrix[i - 1][j], matrix[i][j - 1], matrix[i - 1][j - 1])
    return 1 - matrix[len(str1)][len(str2)] / max(len(str1), len(str2))


with open(args.indir, 'r') as infile:
    dir_files_1 = []
    dir_files_2 = []
    for line in infile.readlines():
        if line != '\n':
            dir_1, dir_2 = line.split()
            dir_files_1.append(dir_1)
            dir_files_2.append(dir_2)

outfile = open(args.outdir, 'a')
for i in range(len(dir_files_1)):
    print(dir_files_1[i], dir_files_2[i])
    try:
        text1 = to_ast('./data/' + dir_files_1[i])
        text2 = to_ast('./data/' + dir_files_2[i])
    except FileNotFoundError:
        continue
    k = antiplagiat(text1, text2)
    print(k)
    outfile.write(str(k) + '\n')
outfile.close()
