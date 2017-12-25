"""
Copyright 2017 Google Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

-------------------------------------------------------------------------------

  Divide the full input list with all dumps into batches.

  Input: input list with all dumps
  Output: batched input list. Each batched input list contain batchsize(current value: 20) dumps.
  Statistics: 25 batches of input lists are generated in the format: 7z_file_list_batched_(batch number).txt under the input_lists folder in dataflow storage.
  Note: This file was running locally to generate the results, the divided input lists were mannually uploaded to cloud storage.
"""

folder = 'input_lists/'
full_list = 'new_7z_file_list.txt'
total = []
with open(folder+full_list) as f:
     for line in f:
         total.append(line[:-1])
cnt = 0
batchsize = 30
batch_no = 3
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

