import codecs
import json
from nltk.tokenize import sent_tokenize, word_tokenize
import re


class TextPreprocessors:
    """
    Contains static methods for taking the json objects and pre-processing/condensing text fields in them
    so they are more suitable for word-embedding code.
    """

    @staticmethod
    def is_sublist_in_big_list(big_list, sublist):
        # matches = []
        for i in range(len(big_list)):
            if big_list[i] == sublist[0] and big_list[i:i + len(sublist)] == sublist:
                return True
        return False

    @staticmethod
    def tokenize_string(string):
        """
        I designed this method to be used independently of an obj/field. If this is the case, call _tokenize_field.
        It's more robust.
        :param string: e.g. 'salt lake city'
        :return: list of tokens
        """
        list_of_sentences = list()
        tmp = list()
        tmp.append(string)
        k = list()
        k.append(tmp)
        # print k
        list_of_sentences += k  # we are assuming this is a unicode/string

        word_tokens = list()
        for sentences in list_of_sentences:
            # print sentences
            for sentence in sentences:
                for s in sent_tokenize(sentence):
                    word_tokens += word_tokenize(s)

        return word_tokens

    @staticmethod
    def _tokenize_field(obj, field):
        """
        At present, we'll deal with only one field (e.g. readability_text). The field could be a unicode
        or a list, so make sure to take both into account.

        We are not preprocessing the tokens in any way. For this, I'll write another function.
        :param obj: the adultservice json object
        :param field: e.g. 'readability_text'
        :return: A list of tokens.
        """
        list_of_sentences = list()

        #print obj['readability_text']
        if field not in obj:
            return None
        elif type(obj[field]) == list:
            k = list()
            k.append(obj[field])
            list_of_sentences += k
        else:
            tmp = list()
            tmp.append(obj[field])
            k = list()
            k.append(tmp)
            # print k
            list_of_sentences += k  # we are assuming this is a unicode/string

        word_tokens = list()
        for sentences in list_of_sentences:
            # print sentences
            for sentence in sentences:
                for s in sent_tokenize(sentence):
                    word_tokens += word_tokenize(s)

        return word_tokens

    @staticmethod
    def _preprocess_tokens(tokens_list, options=['remove_non_alpha','lower']):
        """

        :param tokens_list: The list generated by tokenize_field per object
        :param options: A list of to-dos.
        :return: A list of processed tokens. The original list is unmodified.
        """
        new_list = list(tokens_list)
        for option in options:
            if option == 'remove_non_alpha':
                tmp_list = list()
                for token in new_list:
                    if token.isalpha():
                        tmp_list.append(token)
                del new_list
                new_list = tmp_list
            elif option == 'lower':
                for i in range(0, len(new_list)):
                    new_list[i] = new_list[i].lower()
            else:
                print 'Warning. Option not recognized: '+option

        return new_list

    @staticmethod
    def _preprocess_sampled_annotated_file(sample_file, output_file):
        """
        We sampled files in FieldAnalyses.sample_n_values_from_field, and then labeled them. The problem is
        that we sampled raw values, and now I've done too much labeling to rectify. This is a one-time piece of
         code for the two files we have already sampled/labeled.
        :param sample_file:
        :return:
        """
        out = codecs.open(output_file, 'w', 'utf-8')
        with codecs.open(sample_file, 'r', 'utf-8') as f:
            for line in f:
                fields = re.split('\t',line)
                word_tokens = list()
                for s in sent_tokenize(fields[0]):
                    word_tokens += word_tokenize(s)
                fields[0] = ' '.join(word_tokens)
                out.write('\t'.join(fields))
        out.close()

    @staticmethod
    def _extract_name_strings_from_dict_lists(obj, field='telephone', return_as_tokens = False):
        """
        We're assuming that obj contains 'field' (make sure to have checked for this) which is a list
        containing dicts. Each dict contains a name field. We will return a string of phone numbers in
        alphabetic order.
        :param obj:
        :param field: e.g. telephone or email
        :param return_as_tokens: if True we will return a list, otherwise we'll join and return as string.
        :return: A string, (sorted) list of unique tokens or None (if no names exist within the list)
        """
        phones = set()
        for phone in obj[field]:
            if 'name' in phone and phone['name']:
                if type(phone['name']) == list:
                    phones = phones.union(set(phone['name']))
                else:
                    phones.add(phone['name'])
        if not phones:
            return None
        else:
            phones = list(phones)
            phones.sort()
            if return_as_tokens:
                return phones
            else:
                return '-'.join(phones)

    @staticmethod
    def build_tokens_objects_from_readability(input_file, output_file):
        """

        :param input_file: A json lines file
        :param output_file: A tokens file
        :return: None
        """
        field = 'readability_text'
        out = codecs.open(output_file, 'w', 'utf-8')
        with codecs.open(input_file, 'r', 'utf-8') as f:
            for line in f:
                tokens_obj = dict()
                obj = json.loads(line)
                tokenized_field = TextPreprocessors._tokenize_field(obj, field)
                if tokenized_field:
                    tokens_obj[obj['identifier']] = TextPreprocessors._preprocess_tokens(tokenized_field, options=["lower"])
                    json.dump(tokens_obj, out)
                    out.write('\n')
        out.close()

    @staticmethod
    def build_tokens_objects_from_nyu_data(input_file, output_file):
        """
        We only perform lower-case preprocessing for the moment.
        :param input_file: contains a single json object with keys (URIs) referencing long strings of scraped text.
        :param output_file: a tokens json lines file, with a key referencing a list of tokens.
        :return: None
        """
        inFile = codecs.open(input_file, 'r', 'utf-8')
        outFile = codecs.open(output_file, 'w', 'utf-8')
        obj = json.load(inFile)
        for k,v in obj.items():
            tmp = dict()
            tokenized_field = TextPreprocessors.tokenize_string(v)
            tmp[k] = TextPreprocessors._preprocess_tokens(tokenized_field, options=["lower"])
            json.dump(tmp, outFile)
            outFile.write('\n')
        inFile.close()
        outFile.close()

    @staticmethod
    def combine_jsons(input_files, output_file):
        """
        will raise an exception if keys clash across input files. Also, is memory intensive at present, will
        read in all jsons from the input_files before doing any writing. Thus, relative ordering may not be maintained.
        :param input_files: A list of files, with each file being  a json (not jlines) file
        :param output_file: An output file
        :return: None
        """
        big_dict = dict()
        for f in input_files:
            inFile = codecs.open(f, 'r', 'utf-8')
            TextPreprocessors.merge_dicts(big_dict, json.load(inFile))
            inFile.close()
        outFile = codecs.open(output_file, 'w', 'utf-8')
        json.dump(big_dict, outFile)
        outFile.close()

    @staticmethod
    def merge_dicts(dict_1, dict_2):
        """
        Merges dict_2 into dict_1 (hence, transforms dict_1). Only performs merging at upper level. Will raise exception if keys clash
        :param dict_1:
        :param dict_2:
        :return: None
        """
        for k, v in dict_2.items():
            if k in dict_1:
                raise Exception
            else:
                dict_1[k] = v


    @staticmethod
    def build_phone_objects_from_all_fields(input_file, output_file, exclude_fields = None, exclude_field_regex = None):
        """
        Be careful about the assumptions for the field structure. This function is not going to be appropriate for
        every jlines file.
        :param input_file: A json lines file
        :param output_file: A tokens file, where an identifier has two fields: tokens and phone. Both are lists. Be
        careful about usage; we will use this file primarily for generating phone embeddings.
        :param exclude_fields: If the field is within this list, we will ignore that field.
        :param exclude_field_regex: a regex string, where, if the field name matches this regex, we ignore it.
        :return: None
        """
        # field = 'readability_text'
        out = codecs.open(output_file, 'w', 'utf-8')
        with codecs.open(input_file, 'r', 'utf-8') as f:
            for line in f:
                obj = json.loads(line)

                # get phone string, if one exists
                if 'telephone' not in obj:
                    continue
                else:
                    phone = TextPreprocessors._extract_name_strings_from_dict_lists(obj)
                    if not phone:
                        continue

                # get tokens list, if one exists
                tokens_list = []
                for k in obj.keys():
                    if k == 'telephone':
                        continue
                    if exclude_fields:
                        if k in exclude_fields:
                            continue
                    if exclude_field_regex:
                        pat = re.split(exclude_field_regex, k)
                        print pat
                        if not (pat and len(pat) == 1 and pat[0] == k):
                            continue
                    # print k
                    if k == 'email':
                        tokenized_field = TextPreprocessors._extract_name_strings_from_dict_lists(obj, 'email', True)
                    else:
                        tokenized_field = TextPreprocessors._tokenize_field(obj, k)
                    if tokenized_field:
                        tokens = TextPreprocessors._preprocess_tokens(tokenized_field, options=["lower"])
                        if tokens:
                            tokens_list += tokens

                if not tokens_list:
                    continue

                # assuming we made it this far, we have everything we need
                inner_obj = dict()
                inner_obj['phone'] = phone
                inner_obj['tokens_list'] = tokens_list
                tokens_obj = dict()
                tokens_obj[obj['identifier']] = inner_obj
                json.dump(tokens_obj, out)
                out.write('\n')
        out.close()

    @staticmethod
    def convert_txt_dict_to_json(input_file, output_file):
        results = list()
        with codecs.open(input_file, 'r', 'utf-8') as f:
            for line in f:
                results.append(line[0:-1])
        out = codecs.open(output_file, 'w', 'utf-8')
        json.dump(results, out, indent=4)
        out.close()

    @staticmethod
    def preprocess_annotated_cities_file(input_file, output_file):
        """
        We will take in a file such as annotated-cities-1.json as input and output another json that:
        tokenizes the high_recall_readability_text field and converts it to lower-case.
        converts values in the other two fields to lowercase

        These preprocessed files can then be used for analysis.

        Note that the field names remain the same in the output file, even though high_recall-* is now
         a list of tokens instead of a string.
        :param input_file:
        :param output_file:
        :return:
        """
        out = codecs.open(output_file, 'w', 'utf-8')
        with codecs.open(input_file, 'r', 'utf-8') as f:
            for line in f:
                obj = json.loads(line)
                tokenized_field = TextPreprocessors._tokenize_field(obj, 'high_recall_readability_text')
                if tokenized_field:
                    obj['high_recall_readability_text'] = TextPreprocessors._preprocess_tokens(tokenized_field, options=["lower"])
                    for k in obj.keys():
                        obj[k] = TextPreprocessors._preprocess_tokens(obj[k], options=["lower"])
                    json.dump(obj, out)
                    out.write('\n')
        out.close()

    @staticmethod
    def preprocess_annotated_file(input_file, text_field, output_file):
        """
        We will take in a file such as annotated-cities-1.json as input and output another json that:
        tokenizes the text( e.g. high_recall_readability_text field) and converts it to lower-case.
        converts values in all other fields to lowercase

        These preprocessed files can then be used for analysis.

        Note that the field names remain the same in the output file, even though high_recall-* is now
         a list of tokens instead of a string.
        :param input_file:
        :param text_field:
        :param output_file:
        :return:
        """
        out = codecs.open(output_file, 'w', 'utf-8')
        with codecs.open(input_file, 'r', 'utf-8') as f:
            for line in f:
                obj = json.loads(line)
                tokenized_field = TextPreprocessors._tokenize_field(obj, text_field)
                if tokenized_field:
                    obj[text_field] = TextPreprocessors._preprocess_tokens(tokenized_field, options=["lower"])
                    for k in obj.keys():
                        obj[k] = TextPreprocessors._preprocess_tokens(obj[k], options=["lower"])
                    json.dump(obj, out)
                    out.write('\n')
        out.close()



# path='/Users/mayankkejriwal/ubuntu-vm-stuff/home/mayankkejriwal/tmp/'
# data_path = '/Users/mayankkejriwal/datasets/nyu_data/'
# TextPreprocessors.preprocess_annotated_cities_file(path+'raw-data/annotated-cities-2.json',
#                                                 path+'prepped-data/annotated-cities-2-prepped.json')
# TextPreprocessors.convert_txt_dict_to_json(path+'dictionaries/spa-massage-words.txt', path+'dictionaries/spa-massage-words.json')
# TextPreprocessors.combine_jsons([data_path+'pos_ht_data.json',data_path+'neg_ht_data.json'], data_path+'combined_ht_data.json')
# TextPreprocessors.build_tokens_objects_from_nyu_data(data_path+'combined_ht_data.json', data_path+'tokens_combined_ht_onlyLower.json')
# TextPreprocessors.build_tokens_objects_from_readability(path+'part-00000.json', path+'readability_tokens-part-00000-onlyLower.json')
# exclude_fields_1 = ['high_recall_readability_text', 'identifier', 'inferlink_text', 'readability_text', 'seller']
# exclude_field_regex = '\.*_count'
# string = 'readability_text'
# print re.split(exclude_field_regex, string)
# print '-'.join(exclude_fields_1)
# TextPreprocessors.build_phone_objects_from_all_fields(path+'part-00000.json',
# path+'all_tokens-part-00000-onlyLower-1.json', exclude_fields_1, exclude_field_regex)
# print TextPreprocessors.tokenize_string('salt')
