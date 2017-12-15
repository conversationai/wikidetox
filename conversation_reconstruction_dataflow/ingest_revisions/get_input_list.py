full_set = []
short_set = []
folder = 'input_lists/'
full = '7z_file_list_full.txt'
short_10 = '7z_file_list_short_10.txt'
with open(folder + full) as f:
     for line in f:
         full_set.append(line[:-1])
with open(folder + short_10) as f:
     for line in f:
         short_set.append(line[:-1]) 
with open(folder + '7z_file_list_exclude_10.txt', 'w') as w:
     for l in full_set:
         if not(l in short_set):
            w.write(l + '\n')
