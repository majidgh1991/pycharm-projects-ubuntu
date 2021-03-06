# -*- coding: UTF-8 -*-
from random import shuffle
import codecs
import json
import TextAnalyses
import string
import numpy as np

class RandomIndexer:
    """
    Code for implementing the actual random indexing algorithm. Tokens lists and idfs must have been generated.
    """

    @staticmethod
    def read_in_tokens_file(tokens_list_file):
        answer = dict()
        with codecs.open(tokens_list_file, 'r', 'utf-8') as f:
            for line in f:
                obj = json.loads(line)
                for k, v in obj.items():
                    answer[k] = v
        return answer

    @staticmethod
    def _isnonascii_unicode(s):
        return not all(ord(c) < 128 for c in s)

    @staticmethod
    def _ispunct(s):
        return all(c in string.punctuation for c in s)

    @staticmethod
    def _isalphapunct(s):
        return all(c in string.punctuation or c.isalpha() for c in s)

    @staticmethod
    def _find_right_dummy_v2(token):
        """
        The versions should be aligned with _generate_context_vectors and with generate_unigram_embeddings
        :param token:
        :return: One of the dummy strings (see generate_context_vectors_)
        """

        if token.isdigit():
            return 'dummy_num'
        elif token.isalnum() and not token.isalpha() and not token.isdigit():
            return 'dummy_alpha_num'
        elif RandomIndexer._ispunct(token):
            return 'dummy_punct'
        elif RandomIndexer._isalphapunct(token) and not token.isalpha():
            return 'dummy_alpha_punct'
        elif RandomIndexer._isnonascii_unicode(token):
            return 'dummy_unicode'
        else:
            return 'dummy_idf' # it's just a rare word

    @staticmethod
    def _generate_random_sparse_vector(d, non_zero_ratio):
        """
        Suppose d =200 and the ratio is 0.01. Then there will be 2 +1s and 2 -1s and all the rest are 0s.

        Borrowed from lorelei. I've tested this method
        :param d:
        :param non_zero_ratio:
        :return: a vector with d dimensions
        """
        answer = [0]*d
        indices = [i for i in range(d)]
        shuffle(indices)
        k = int(non_zero_ratio*d)
        for i in range(0, k):
            answer[indices[i]] = 1
        for i in range(k, 2*k):
            answer[indices[i]] = -1
        return np.array(answer)

    @staticmethod
    def _generate_context_vectors_for_idf(idf_dict, include_dummy, d, non_zero_ratio):
        """
        Generate context vectors
        :param idf_dict:
        :param include_dummy: If true, then we will append '' as a key in idf_dict, and generate a context
        vector for that as well.
        :param d:
        :param non_zero_ratio:
        :return: A dictionary with idf keys as keys, and a context vector as value.
        """
        context_dict = dict()
        for k in idf_dict.keys():
            context_dict[k] = RandomIndexer._generate_random_sparse_vector(d, non_zero_ratio)
        if include_dummy:
            print 'Don\'t forget, dummy is the empty string'
            if '' in context_dict:
                raise Exception
            else:
                context_dict[''] = RandomIndexer._generate_random_sparse_vector(d, non_zero_ratio)
        return context_dict

    @staticmethod
    def _generate_context_vectors_for_idf_v2(idf_dict, include_dummies, d, non_zero_ratio):
        """
        Generate context vectors. For info on the dummies, see notes.txt
        :param idf_dict:
        :param include_dummies: If true, then we will append several 'dummy' keys in idf_dict, and generate context
        vectors for those as well.
        :param d:
        :param non_zero_ratio:
        :return: A dictionary with idf keys as keys, and a context vector as value.
        """
        context_dict = dict()
        for k in idf_dict.keys():
            context_dict[k] = RandomIndexer._generate_random_sparse_vector(d, non_zero_ratio)
        if include_dummies:
            if 'dummy_punct' in context_dict:
                raise Exception
            else:
                context_dict['dummy_punct'] = RandomIndexer._generate_random_sparse_vector(d, non_zero_ratio)

            if 'dummy_alpha_num' in context_dict:
                raise Exception
            else:
                context_dict['dummy_alpha_num'] = RandomIndexer._generate_random_sparse_vector(d, non_zero_ratio)

            if 'dummy_alpha_punct' in context_dict:
                raise Exception
            else:
                context_dict['dummy_alpha_punct'] = RandomIndexer._generate_random_sparse_vector(d, non_zero_ratio)

            if 'dummy_idf' in context_dict:
                raise Exception
            else:
                context_dict['dummy_idf'] = RandomIndexer._generate_random_sparse_vector(d, non_zero_ratio)

            if 'dummy_num' in context_dict:
                raise Exception
            else:
                context_dict['dummy_num'] = RandomIndexer._generate_random_sparse_vector(d, non_zero_ratio)

            if 'dummy_unicode' in context_dict:
                raise Exception
            else:
                context_dict['dummy_unicode'] = RandomIndexer._generate_random_sparse_vector(d, non_zero_ratio)
        return context_dict

    @staticmethod
    def _init_unigram_embeddings(token_cvs):
        unigram_embeddings = dict()
        for k, v in token_cvs.items():
            # if k == '':  # don't forget to exclude the dummy value (if there)
            #     continue
            # else:
                unigram_embeddings[k] = np.array([0]*len(v))  # deep copy of list
        return unigram_embeddings

    @staticmethod
    def _init_phone_embeddings(inner_field_tokens_file, d):
        """

        :param inner_field_tokens_file: each json in the inner_field file must have a single key-value pair
        of which the value itself is a dictionary with a phone field. This phone field references a string.
        We will initialize each embedding to be the 0 vector
        :param d: the dimensionality of the embedding
        :return: A dictionary of initialized embedding vectors
        """
        phone_embeddings = dict()
        with codecs.open(inner_field_tokens_file, 'r', 'utf-8') as f:
            for line in f:
                obj = json.loads(line)
                phone = obj.values()[0]['phone']
                phone_embeddings[phone] = np.array([0.0]*d)
        return phone_embeddings

    @staticmethod
    def generate_unigram_embeddings_v1(tokens_file, idf_file, output_file=None, context_window_size=2,
                                    include_dummy=True, d=200, non_zero_ratio=0.01):
        """
        We are keeping the lower_prune and upper_prune ratios in the TextAnalyses file. Feel free to change
        those directly. Consider adding weighting scheme in future. Right now, we assume constant weighting
        for the tokens in the context window

        This code does not assume the tokens_file is small enough to fit in memory. Note
        that idf_file data must be read into main memory at the present time.
        :param tokens_file:
        :param idf_file:
        :param output_file: each line will be a dict
        :param context_window_size:
        :param include_dummy:
        :param d:
        :param non_zero_ratio:
        :return:
        """
        idf_dict = TextAnalyses.TextAnalyses.read_in_and_prune_idf(idf_file)
        token_cvs = RandomIndexer._generate_context_vectors_for_idf(idf_dict, include_dummy, d, non_zero_ratio)
        # tokens_dict = RandomIndexer.read_in_tokens_file(tokens_file)
        unigram_embeddings = RandomIndexer._init_unigram_embeddings(token_cvs)
        count = 1
        with codecs.open(tokens_file, 'r', 'utf-8') as f:
            for line in f:
                obj = json.loads(line)
                v = None
                for k, val in obj.items():
                    v = val
                print 'In document '+str(count)
                count += 1
                if count>10000:
                    break
                for i in range(0, len(v)):
                    if v[i] not in token_cvs:
                        continue
                    vec = unigram_embeddings[v[i]]
                    min = i-context_window_size
                    if min<0:
                        min = 0
                    max = i+context_window_size
                    if max>len(v):
                        max = len(v)
                    for j in range(min, max):
                        if j == i:
                            continue
                        context_token = v[j]
                        if context_token not in token_cvs:
                            if include_dummy:
                                context_token = ''
                            else:
                                continue
                        for k in range(0, len(token_cvs[context_token])):
                            vec[k] += token_cvs[context_token][k]
                    unigram_embeddings[v[i]] = vec
        if output_file:
            out = codecs.open(output_file, 'w', 'utf-8')
            for k, v in unigram_embeddings.items():
                answer = dict()
                answer[k] = v
                json.dump(answer, out)
                out.write('\n')
            out.close()

    @staticmethod
    def generate_unigram_embeddings_twitter_v1(tokens_file, idf_file, output_file=None, context_window_size=2,
                                    include_dummy=False, d=20, non_zero_ratio=0.05):
        """

        :param tokens_file:
        :param idf_file:
        :param output_file:
        :param context_window_size:
        :param include_dummies:
        :param d:
        :param non_zero_ratio:
        :return:
        """
        idf_dict = TextAnalyses.TextAnalyses.read_in_and_prune_idf(idf_file, lower_prune_ratio=0.0)
        token_cvs = RandomIndexer._generate_context_vectors_for_idf(idf_dict, include_dummy, d, non_zero_ratio)
        # tokens_dict = RandomIndexer.read_in_tokens_file(tokens_file)
        unigram_embeddings = RandomIndexer._init_unigram_embeddings(token_cvs)
        count = 1
        with codecs.open(tokens_file, 'r', 'utf-8') as f:
            for line in f:
                obj = json.loads(line)
                v = None
                for k, val in obj.items():
                    v = val
                print 'In document '+str(count)
                count += 1
                # if count>10000:
                #     break
                for i in range(0, len(v)):
                    if v[i] not in token_cvs:
                        continue
                    vec = unigram_embeddings[v[i]]
                    min = i-context_window_size
                    if min<0:
                        min = 0
                    max = i+context_window_size
                    if max>len(v):
                        max = len(v)
                    for j in range(min, max):
                        if j == i:
                            continue
                        context_token = v[j]
                        if context_token not in token_cvs:
                            if include_dummy:
                                context_token = ''
                            else:
                                continue
                        for k in range(0, len(token_cvs[context_token])):
                            vec[k] += token_cvs[context_token][k]
                    unigram_embeddings[v[i]] = vec
        if output_file:
            out = codecs.open(output_file, 'w', 'utf-8')
            for k, v in unigram_embeddings.items():
                answer = dict()
                answer[k] = v
                json.dump(answer, out)
                out.write('\n')
            out.close()

    @staticmethod
    def generate_unigram_embeddings_v2(tokens_file, idf_file, output_file=None, context_window_size=2,
                                    include_dummies=True, d=200, non_zero_ratio=0.01,lower_prune_ratio=0.0005, upper_prune_ratio=0.7, max_length=1000):
        """
        We are keeping the lower_prune and upper_prune ratios in the TextAnalyses file. Feel free to change
        those directly. Consider adding weighting scheme in future. Right now, we assume constant weighting
        for the tokens in the context window

        This code does not assume the tokens_file is small enough to fit in memory. Note
        that idf_file data must be read into main memory at the present time.

        The difference between v1 and v2 is that we now accommodate more dummy variables. The goal is that
        we should have vector representations for every token (no matter how bad). For the dummies I've
        considered so far, consult notes.txt (Sept. 6th entry)
        :param tokens_file:
        :param idf_file:
        :param output_file: each line will be a dict
        :param context_window_size:
        :param include_dummies:
        :param d:
        :param non_zero_ratio:
        :return:
        """
        idf_dict = TextAnalyses.TextAnalyses.read_in_and_prune_idf(idf_file, lower_prune_ratio, upper_prune_ratio)
        token_cvs = RandomIndexer._generate_context_vectors_for_idf_v2(idf_dict, include_dummies, d, non_zero_ratio)
        print 'finished generating context vectors...'
        # tokens_dict = RandomIndexer.read_in_tokens_file(tokens_file)
        unigram_embeddings = RandomIndexer._init_unigram_embeddings(token_cvs)
        print 'finished initializing embeddings vectors...'
        count = 1
        with codecs.open(tokens_file, 'r', 'utf-8') as f:
            for line in f:
                obj = json.loads(line)
                v = None
                for k, val in obj.items():
                    v = val
                if count%500==0:
                    print 'In document '+str(count)
                count += 1
                k=None
                # if count>100:
                #     break
                # limit = len(v)
                increment = 1
                if max_length:
                    if len(v) > max_length:
                        increment = len(v) / max_length
                # elif len(v) > 1000:
                #     increment = len(v)/1000
                for i in range(0, len(v), increment):
                    token = v[i]
                    if token not in token_cvs:
                        if include_dummies:
                            token = RandomIndexer._find_right_dummy_v2(token)
                            vec = unigram_embeddings[token]
                        else:
                            continue
                    else:
                        vec = unigram_embeddings[token]
                    min = i-context_window_size
                    if min<0:
                        min = 0
                    max = i+context_window_size
                    if max>len(v):
                        max = len(v)
                    context_window_vecs = list()
                    for j in range(min, max):
                        if j == i:
                            continue
                        context_token = v[j]
                        if context_token not in token_cvs:
                            if include_dummies:
                                context_token = RandomIndexer._find_right_dummy_v2(context_token)
                            else:
                                continue
                        context_window_vecs.append(token_cvs[context_token])
                        # for k in range(0, len(token_cvs[context_token])):
                    context_window_vecs.append(vec)
                    unigram_embeddings[token] = np.sum(context_window_vecs,axis=0)

        if output_file:
            out = codecs.open(output_file, 'w', 'utf-8')
            for k, v in unigram_embeddings.items():
                answer = dict()
                answer[k] = v.tolist()
                json.dump(answer, out)
                out.write('\n')
            out.close()

    @staticmethod
    def generate_unigram_embeddings_v1_batch(tokens_file, idf_file, output_file=None, context_window_size=2,
                                    include_dummy=True, d=200, non_zero_ratio=0.01):
        """
        We are keeping the lower_prune and upper_prune ratios in the TextAnalyses file. Feel free to change
        those directly. Consider adding weighting scheme in future. Right now, we assume constant weighting
        for the tokens in the context window

        This is in batch mode because the entire input file (tokens_file) is read into main memory
        before processing is done. If this file is too big, please use the non-batch version. Note
        that idf_file data must be read into main memory at the present time.
        :param tokens_file:
        :param idf_file:
        :param output_file: each line will be a dict
        :param context_window_size:
        :param include_dummy:
        :param d:
        :param non_zero_ratio:
        :return:
        """
        idf_dict = TextAnalyses.TextAnalyses.read_in_and_prune_idf(idf_file)
        token_cvs = RandomIndexer._generate_context_vectors_for_idf(idf_dict, include_dummy, d, non_zero_ratio)
        tokens_dict = RandomIndexer.read_in_tokens_file(tokens_file)
        unigram_embeddings = RandomIndexer._init_unigram_embeddings(token_cvs)
        count = 1
        for v in tokens_dict.itervalues():
            print 'In document '+str(count)
            count += 1
            for i in range(0, len(v)):
                if v[i] not in token_cvs:
                    continue
                vec = unigram_embeddings[v[i]]
                min = i-context_window_size
                if min<0:
                    min = 0
                max = i+context_window_size
                if max>len(v):
                    max = len(v)
                for j in range(min, max):
                    if j == i:
                        continue
                    context_token = v[j]
                    if context_token not in token_cvs:
                        if include_dummy:
                            context_token = ''
                        else:
                            continue
                    for k in range(0, len(token_cvs[context_token])):
                        vec[k] += token_cvs[context_token][k]
                unigram_embeddings[v[i]] = vec
        if output_file:
            out = codecs.open(output_file, 'w', 'utf-8')
            for k, v in unigram_embeddings.items():
                answer = dict()
                answer[k] = v
                json.dump(answer, out)
                out.write('\n')
            out.close()

    @staticmethod
    def generate_telephone_embeddings_v1(inner_field_tokens_file, idf_file, output_file,
                                         include_dummies=False, d=200, non_zero_ratio=0.01):
        """

        :param inner_field_tokens_file:
        :param idf_file:
        :param output_file:
        :param include_dummies:
        :param d:
        :param non_zero_ratio:
        :return:
        """
        idf_dict = TextAnalyses.TextAnalyses.read_in_and_prune_idf(idf_file, lower_prune_ratio=0.0)
        token_cvs = RandomIndexer._generate_context_vectors_for_idf_v2(idf_dict, include_dummies, d, non_zero_ratio)
        phone_embeddings = RandomIndexer._init_phone_embeddings(inner_field_tokens_file, d=d)
        count = 1
        with codecs.open(inner_field_tokens_file, 'r', 'utf-8') as f:
            for line in f:
                obj = json.loads(line)
                v = obj.values()[0]['tokens_list']

                print 'In document ' + str(count)
                count += 1
                # if count>10000:
                #     break
                phone = obj.values()[0]['phone']
                for token in v:
                    if token not in token_cvs:
                        if include_dummies:
                            token = RandomIndexer._find_right_dummy_v2(token)
                            vec = token_cvs[token]
                        else:
                            continue
                    else:
                        vec = token_cvs[token]

                    for k in range(0, len(phone_embeddings[phone])):
                        phone_embeddings[phone][k] += vec[k]

        if output_file:
            out = codecs.open(output_file, 'w', 'utf-8')
            for k, v in phone_embeddings.items():
                answer = dict()
                answer[k] = v
                json.dump(answer, out)
                out.write('\n')
            out.close()

    @staticmethod
    def generate_RWP_sliced_unigram_embeddings_v2(tokens_file, idf_file, output_folder_prefix, summary_output_file,
            context_window_size=2, include_dummies=True, d=200, non_zero_ratio=0.01, slice_window_size=100):
        """
        Introduces a new parameter (slice_window_size). Currently, I am only using this for RWP. However, the
        function can be generalized to work on other 'lorelei' datasets.

        We are keeping the lower_prune and upper_prune ratios in the TextAnalyses file. Feel free to change
        those directly. Consider adding weighting scheme in future. Right now, we assume constant weighting
        for the tokens in the context window

        This code does not assume the tokens_file is small enough to fit in memory. Note
        that idf_file data must be read into main memory at the present time.

        The difference between v1 and v2 is that we now accommodate more dummy variables. The goal is that
        we should have vector representations for every token (no matter how bad). For the dummies I've
        considered so far, consult notes.txt (Sept. 6th entry)


        :param tokens_file:
        :param idf_file:
        :param output_folder_prefix: prefix for where the sliced embeddings will get written out
        :param summary_output_file: the details summarizing what are in the output folder. It will be a jl file. We will
        record (as lists) in each json the uuids and the name of the file to which the embeddings for written.
        :param context_window_size:
        :param include_dummies:
        :param d:
        :param non_zero_ratio:
        :param slice_window_size: see the RWP embeddings data we generated to get an idea of what this means.
        note that the window is NOT sliding. The output_file
        :return:
        """
        idf_dict = TextAnalyses.TextAnalyses.read_in_and_prune_idf(idf_file, lower_prune_ratio=0.0005,
                                                                   upper_prune_ratio=0.5)
        token_cvs = RandomIndexer._generate_context_vectors_for_idf_v2(idf_dict, include_dummies, d, non_zero_ratio)
        # remember, context vectors must only be generated once!
        # tokens_dict = RandomIndexer.read_in_tokens_file(tokens_file)
        unigram_embeddings = RandomIndexer._init_unigram_embeddings(token_cvs)
        uuids_list = list()
        local_count = 1
        global_count = 1
        embed_count = 1
        summary_out = codecs.open(summary_output_file, 'w', 'utf-8')
        with codecs.open(tokens_file, 'r', 'utf-8') as f:
            for line in f:
                obj = json.loads(line)
                v = None
                for k, val in obj.items():
                    v = val
                    uuids_list.append(k)
                print 'In document ' + str(global_count)

                for i in range(0, len(v)):
                    token = v[i]
                    if token not in token_cvs:
                        if include_dummies:
                            token = RandomIndexer._find_right_dummy_v2(token)
                            vec = unigram_embeddings[token]
                        else:
                            continue
                    else:
                        vec = unigram_embeddings[token]
                    min = i - context_window_size
                    if min < 0:
                        min = 0
                    max = i + context_window_size
                    if max > len(v):
                        max = len(v)
                    for j in range(min, max):
                        if j == i:
                            continue
                        context_token = v[j]
                        if context_token not in token_cvs:
                            if include_dummies:
                                context_token = RandomIndexer._find_right_dummy_v2(context_token)
                            else:
                                continue
                        for k in range(0, len(token_cvs[context_token])):
                            vec[k] += token_cvs[context_token][k]
                    unigram_embeddings[token] = vec

                if local_count>=slice_window_size:
                    local_count = 1
                    embed_file = output_folder_prefix+str(embed_count)+'.json'
                    embed_out = codecs.open(embed_file, 'w', 'utf-8')
                    for kk, vv in unigram_embeddings.items():
                        answer = dict()
                        answer[kk] = vv
                        json.dump(answer, embed_out)
                        embed_out.write('\n')
                    embed_out.close()
                    summary_answer = dict()
                    summary_answer['uuids'] = uuids_list
                    summary_answer['embedding_file'] = embed_file
                    json.dump(summary_answer, summary_out)
                    summary_out.write('\n')
                    del summary_answer
                    del unigram_embeddings
                    del uuids_list
                    uuids_list = list()
                    unigram_embeddings = RandomIndexer._init_unigram_embeddings(token_cvs)
                    embed_count += 1
                else:
                    local_count += 1

                global_count += 1


        summary_out.close()

# str = 'bødy'
# print str.isalpha()
# print RandomIndexer._find_right_dummy_v2(u'...')
# CP1SummerPath = '/Users/mayankkejriwal/datasets/memex-evaluation-november/CP-1-november/'
# path = '/Users/mayankkejriwal/ubuntu-vm-stuff/home/mayankkejriwal/tmp/www-experiments/embeddings/'
# RWP_path = '/Users/mayankkejriwal/ubuntu-vm-stuff/home/mayankkejriwal/Downloads/lorelei/reliefWebProcessed-prepped/'
# data_path = '/Users/mayankkejriwal/datasets/memex-evaluation-november/persona-linking/'
# companiesTextPath = '/Users/mayankkejriwal/datasets/companies/'
# idf_dict = TextAnalyses.TextAnalyses.read_in_and_prune_idf(data_path+'tokens-all-df.txt',
# lower_prune_ratio=0.01, upper_prune_ratio=0.1)
# idf_dict = TextAnalyses.TextAnalyses.read_in_and_prune_idf(data_path+'hrr_df.txt', lower_prune_ratio=0.0005, upper_prune_ratio=0.7)
# bioInfoPath = '/Users/mayankkejriwal/datasets/bioInfo/2016-11-08-intact_mgi_comparison/'
# RandomIndexer.generate_RWP_sliced_unigram_embeddings_v2(data_path+'lowerCaseTokens-sorted.json',
#                      data_path+'df.txt', data_path+'slice-100/unigrams-v2-', data_path+'slice-100-summary.json')
# RandomIndexer.generate_unigram_embeddings_v2(data_path+'tokens-all.jl',
#                                              data_path+'tokens-all-df.txt',
#                                              data_path+'tokens-all-unigram-v2-liberal.json',lower_prune_ratio=0.001,
#                                              upper_prune_ratio=0.1, max_length=None)
# RandomIndexer.generate_unigram_embeddings_v2(data_path+'hrr_output_all.jl',
#                                              data_path+'hrr_df.txt',
#                                              data_path+'hrr_unigram-v2.json')
# RandomIndexer.generate_unigram_embeddings_v2(companiesTextPath+'result-prepped.jl',companiesTextPath+'result_df.txt',
#                                         companiesTextPath+'result-unigram-v2.jl',d=100)
# RandomIndexer.generate_unigram_embeddings_v2(bioInfoPath+'mgiPos_intactNeg_tokens.jl',bioInfoPath+'mgiIntact_df.txt',
#                                         bioInfoPath+'mgiIntact_unigram-v2.jl', d=100, non_zero_ratio=0.01,
#                                             lower_prune_ratio=0.0, upper_prune_ratio=1.0, max_length=None)
# RandomIndexer.generate_unigram_embeddings_v2(CP1SummerPath+'positive_tokens.json',
#                                              CP1SummerPath+'CP1_november_positive_df.txt',
#                                         CP1SummerPath+'CP1Positive_unigram-v2.jl', d=200, non_zero_ratio=0.01,
#                                             lower_prune_ratio=0.00005, upper_prune_ratio=0.4, max_length=None)
# RandomIndexer.generate_telephone_embeddings_v1(path+'all_tokens-part-00000-onlyLower-1.json',
#                                              path+'all_tokens-part-00000-onlyLower-1-df.txt',
#                                              path+'phone-embeddings-part-00000-v1.json')
# RandomIndexer.generate_unigram_embeddings_twitter_v1(path+'tokens/ebolaXFer_lowerCase.json',
#                         path+'tokens/ebolaXFer_lowerCase_df.txt',
#               path+'embedding/unigram-embeddings-v2.json')

