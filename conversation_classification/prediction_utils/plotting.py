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
"""


import matplotlib.pyplot as plt
import scipy.stats
import numpy as np

def attacker_plot(profiles, ASPECTS, num_categories=3, \
    catergories={'Min': 0, 'Max': 1, 'In the Middle': 2, 'Anonymous':3, 'New Comer':4, 'No Gap': 5, 'Bot': 6},\
    cats = ['Min', 'Max', 'In the Middle', 'Anonymous', 'New Comer'], experience=-1):

    f, ax = plt.subplots(1, figsize=(20,10))
    bar_width = 0.4
    bar_l = [i for i in range(len(ASPECTS))] 
    tick_pos = [i+bar_width for i in bar_l]

    colors = ['pink', 'mediumslateblue', 'steelblue', 'mediumaquamarine', 'darksalmon']
    bads = [[[], [], [], [], [], [], []], [[], [], [], [], [], [], []]]
    total = len(profiles[0])
    alpha=[0.9, 0.3]
    conv_label = ['bad_', 'good_']
    mins = [[], []]
    cnts = [[[], [], [], [], [], [], []], [[], [], [], [], [], [], []]]
    rects = []
    for clss in [0, 1]:
        for aspect in ASPECTS:
            cur = []
            for ind in range(len(catergories)):
                bads[clss][ind].append(0)
                cnts[clss][ind].append(0)
            for p in profiles[clss]:
                bads[clss][catergories[p[aspect]]][-1] += 1
                cnts[clss][catergories[p[aspect]]][-1] += 1
                if catergories[p[aspect]] == 0:
                    cur.append(1)
                elif catergories[p[aspect]] < num_categories:
                    cur.append(0)
            mins[clss].append(cur)
        previous = [0 for a in ASPECTS]
        first_three = [0 for a in ASPECTS]
        for bad in bads[clss][:num_categories]:
            for ii, b in enumerate(bad):
                first_three[ii] += b
        for ind,bad in enumerate(bads[clss][:num_categories]):
            for ii, b in enumerate(bad):
                if first_three[ii]: bad[ii] = bad[ii] / first_three[ii]
            bads[clss][ind] = bad
            rects = ax.bar(bar_l, bad, label=conv_label[clss] + cats[ind], bottom = previous, alpha=alpha[clss], \
                color=colors[ind],width=bar_width,edgecolor='white')
            for ind, rect in enumerate(rects):
                ax.text(rect.get_x() + rect.get_width()/2., (bad[ind] / 3 + previous[ind]),
                '%.2f' % bad[ind],
                ha='center', va='bottom')
            for ii, b in enumerate(bad):
                previous[ii] += b
        ax.legend(loc="upper left", bbox_to_anchor=(1,1), fontsize='small')
        bar_l = [b+bar_width for b in bar_l]
        if clss:
            print('Good Total:')
        else:
            print('Bad Total:')
        for ii,aspect in enumerate(ASPECTS):
            print(aspect, first_three[ii])
    ax.set_ylabel("Percentage among All the Cases")
    ax.set_xlabel("Aspect")
    Xticks = ASPECTS

    plt.xticks(tick_pos, Xticks)

    # rotate axis labels
    plt.setp(plt.gca().get_xticklabels(), rotation=25, horizontalalignment='right')
    plt.title('Who\'s the Attacker')

    # shot plot
    plt.show()

    print('Test 1')
    for ind, aspect in enumerate(ASPECTS):
        print(aspect)
        print('Average in Ggap: ', np.mean(mins[1][ind]))
        print('Average of Bgap: ', np.mean(mins[0][ind]))
        if np.mean(mins[1][ind]) == 1 or np.mean(mins[1][ind]) == 0:
            continue
        print(scipy.stats.mannwhitneyu(mins[0][ind], mins[1][ind]))
        print('\n')
    print('Test 2')
    clss = 0
    for ind, aspect in enumerate(ASPECTS):
        print(aspect, ':', scipy.stats.binom_test(cnts[clss][0][ind], cnts[clss][0][ind] + cnts[clss][1][ind]))
     #   print(cnts[clss][0][ind], cnts[clss][1][ind])
    print('\n')
    print('Test 3')
    clss = 1
    for ind, aspect in enumerate(ASPECTS):
        print(aspect, ':', scipy.stats.binom_test(cnts[clss][0][ind], cnts[clss][0][ind] + cnts[clss][1][ind]))
    
def plot_profiles(profiles, ASPECTS, num_categories = 3, \
    catergories = {'Min': 0, 'Max': 1, 'In the Middle': 2, 'Anonymous':3, 'New Comer':4, 'No Gap': 5, 'Bot': 6}, \
    cats = ['min', 'max', 'in the middle', 'Anonymous', 'New Comer'], \
    catergory_names = ['Proportion replied', 'Being replied latency', 'Reply latency', \
            'Age', 'Status', '# edits on Wikipedia'], \
    conv_label = ['Offender is ', 'Non-offender is '], \
    experience=-1):
    """
      Plots the profiles of the last participant of a conversation.
      With respect to each aspect(for example, age), how much percentage of the conversations with last participant being the youngest/ordest/in the middle/there's no age gap in the group/the last participant never spoke in the conversation before/the last participant is anonymous or a bot.
    """
    f, ax = plt.subplots(1, figsize=(13,6))
    bar_width = 0.4
    bar_l = [i for i in range(len(ASPECTS))] 
    tick_pos = [i+bar_width for i in bar_l]

    colors = ['pink', 'mediumslateblue', 'steelblue', 'mediumaquamarine', 'darksalmon']
    bads = [[[], [], [], [], [], [], []], [[], [], [], [], [], [], []]]
    total = len(profiles[0])
    alpha=[0.9, 0.3]
    mins = [[], []]
    cnts = [[[], [], [], [], [], [], []], [[], [], [], [], [], [], []]]
    rects = []
    for clss in [0, 1]:
        for aspect in ASPECTS:
            cur = []
            for ind in range(len(catergories)):
                bads[clss][ind].append(0)
                cnts[clss][ind].append(0)
            for p in profiles[clss]:
                bads[clss][catergories[p[aspect]]][-1] += 1
                cnts[clss][catergories[p[aspect]]][-1] += 1
                if catergories[p[aspect]] == 0:
                    cur.append(1)
                elif catergories[p[aspect]] < num_categories:
                    cur.append(0)
            mins[clss].append(cur)
        previous = [0 for a in ASPECTS]
        first_three = [0 for a in ASPECTS]
        for bad in bads[clss][:num_categories]:
            for ii, b in enumerate(bad):
                first_three[ii] += b
        for ind,bad in enumerate(bads[clss][:num_categories]):
            for ii, b in enumerate(bad):
                if first_three[ii]: bad[ii] = bad[ii] / first_three[ii]
            bads[clss][ind] = bad
            rects = ax.bar(bar_l, bad, label=conv_label[clss] + cats[ind], bottom = previous, alpha=alpha[clss], \
                color=colors[ind],width=bar_width,edgecolor='white')
            for ind, rect in enumerate(rects):
                ax.text(rect.get_x() + rect.get_width()/2., (bad[ind] / 3 + previous[ind]),
                '%.1f' % (bad[ind]*100) + '%',
                ha='center', va='bottom')
            for ii, b in enumerate(bad):
                previous[ii] += b
        ax.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
       ncol=3, mode="expand", borderaxespad=0., fontsize='large')
        bar_l = [b+bar_width for b in bar_l]
        if clss:
            print('Good Total:')
        else:
            print('Bad Total:')
        for ii,aspect in enumerate(ASPECTS):
            print(aspect, first_three[ii])
    ax.set_ylabel("Percentage among All the Cases", fontsize='large')
    Xticks = catergory_names
    plt.xticks([t - bar_width / 2 for t in tick_pos], Xticks, fontsize='large')
    plt.setp(plt.gca().get_xticklabels(), rotation=20, horizontalalignment='right')

    plt.show()
    print('Test 1')
    for ind, aspect in enumerate(ASPECTS):
        print(aspect)
        print('Average in Ggap: ', np.mean(mins[1][ind]))
        print('Average of Bgap: ', np.mean(mins[0][ind]))
        if np.mean(mins[1][ind]) == 1 or np.mean(mins[1][ind]) == 0:
            continue
        print(scipy.stats.mannwhitneyu(mins[0][ind], mins[1][ind]))
        print('\n')
    print('Test 2')
    clss = 0
    for ind, aspect in enumerate(ASPECTS):
        print(aspect, ':', scipy.stats.binom_test(cnts[clss][0][ind], cnts[clss][0][ind] + cnts[clss][1][ind]))
    print('\n')
    print('Test 3')
    clss = 1
    for ind, aspect in enumerate(ASPECTS):
        print(aspect, ':', scipy.stats.binom_test(cnts[clss][0][ind], cnts[clss][0][ind] + cnts[clss][1][ind]))
