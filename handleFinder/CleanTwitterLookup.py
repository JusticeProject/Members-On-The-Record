input = open("../output/TwitterLookup.txt", "r", encoding="utf-8")
lines = input.readlines()
input.close()

output = open("../config/TwitterLookupClean.txt", "w", encoding="utf-8")

for line in lines:
    line_split = line.strip().split(",")
    output.write(line_split[0] + "\n")

output.close()
