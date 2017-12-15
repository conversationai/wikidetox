folder = 'input_lists/'
full_list = '7z_file_list_exclude_10.txt'
total = []
with open(folder+full_list) as f:
     for line in f:
         total.append(line[:-1])
cnt = 0
batchsize = 20
batch_no = 0
file_list = []
for line in total:
    if cnt == batchsize:  
       with open((folder + '7z_file_list_batched_%d')%(batch_no), 'w') as w:
            for f in file_list: 
                w.write(f + '\n')
       batch_no += 1
       file_list = []
       cnt = 0
    cnt += 1
    file_list.append(line)
if not(file_list == []):  
   with open((folder + '7z_file_list_batched_%d')%(batch_no), 'w') as w:
        for f in file_list: 
            w.write(f + '\n')

