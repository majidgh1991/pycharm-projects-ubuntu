import codecs
import re
import TextPreprocessors
import kNearestNeighbors


class SampleFilePreprocessors:
    """
    We will use this for preprocessing/prepping the sample files generated by field analyses (and possibly norm.)
    in TextPreprocessors. The first goal of the preprocessing is to ensure we have a list of words
    from the embeddings that are 'positive' and a list that are 'negative' with respect to a given class.

     An initial important step is to ensure our sample files meet the correct formatting requirements. This
     varies depending on which sample file we're looking at.
    """
    @staticmethod
    def _check_ethnicity_sample_file(sample_file):
        """

        :param sample_file:
        :return:
        """
        with codecs.open(sample_file, 'r', 'utf-8') as f:
            for line in f:
                fields = re.split('\t',line)
                if fields[1][0:-1] == 'nr':
                    if len(fields) != 2:
                        print 'error 1 in line : ',
                        print line
                    continue
                elif fields[1] != 'r' and len(fields) != 4:
                    print 'error 2 in line : ',
                    print line
                    continue
                elif fields[2] != 'ethnicity' and fields[2] != 'both':
                    print 'error 3 in line : ',
                    print line
                    continue
                else:
                    big = set(re.split(' ',fields[0]))
                    small = set(re.split(',',fields[3][0:-1]))
                    if len(small.difference(big)) != 0:
                        print 'error 4 in line : ',
                        print line
                        continue

    @staticmethod
    def _check_eyeColor_sample_file(sample_file):
        """

        :param sample_file:
        :return:
        """
        with codecs.open(sample_file, 'r', 'utf-8') as f:
            for line in f:
                fields = re.split('\t',line)
                if fields[1][0:-1] == 'nr':
                    if len(fields) != 2:
                        print 'error 1 in line : ',
                        print line
                    continue
                elif fields[1] != 'r' and len(fields) != 3:
                    print 'error 2 in line : ',
                    print line
                    continue
                else:
                    big = set(re.split(' ',fields[0]))
                    small = set(re.split(',',fields[2][0:-1]))
                    if len(small.difference(big)) != 0:
                        print 'error 3 in line : ',
                        # print small
                        # print big
                        print line
                        continue

    @staticmethod
    def _check_embeddings_coverage(sample_file, embeddings_file,
                                   preprocess_function=TextPreprocessors.TextPreprocessors._preprocess_tokens):
        """
        Designed for any sample file. Will first read in all tokens (using space as separator) from the first
        column of sample_file, and if preprocess_function is not None, will preprocess the token list.
        Next, we'll read in the embeddings file and compute token coverage.

        Note that if multiple tokens appear in some line, it will be as if they are differnt lines. This is because
        each token would be a separate 'instance' in any ML algorithm we use.
        :param sample_file:
         :param embeddings_file:
         :param preprocess_function: a function
        :return: None
        """
        list_of_r_tokens = list()
        list_of_nr_tokens = list()
        with codecs.open(sample_file, 'r', 'utf-8') as f:
            for line in f:
                cols = re.split('\t',line)
                first_field = cols[0]
                fields = re.split(' ',first_field)
                if preprocess_function:
                    fields = (preprocess_function(fields))
                if cols[1] == 'r':
                    list_of_r_tokens += fields
                elif cols[1] == 'nr\n':
                    list_of_nr_tokens += fields
                else:
                    print 'Error in line! Run sample validation code'
        embeddings = set(kNearestNeighbors.read_in_embeddings(embeddings_file).keys())
        covered_r = 0
        covered_nr = 0
        for r in list_of_r_tokens:
            if r in embeddings:
                covered_r += 1
        for nr in list_of_nr_tokens:
            if nr in embeddings:
                covered_nr += 1
        print 'Covered r is '+str(covered_r)+' out of a total of '+str(len(list_of_r_tokens))+' tokens'
        print 'Covered nr is '+str(covered_nr)+' out of a total of '+str(len(list_of_nr_tokens))+' tokens'

    @staticmethod
    def filter_r_lines(sample_file, embeddings_file, output_file,
                                   preprocess_function=TextPreprocessors.TextPreprocessors._preprocess_tokens):
        """
        The goal of this function is to take a sample file, and to print to file all 'r' annotated lines
        such that at least some token from the last column has an embedding.
        :param sample_file:
        :param embeddings_file:
        :param output_file:
        :param preprocess_function:
        :return:
        """
        embeddings = set(kNearestNeighbors.read_in_embeddings(embeddings_file).keys())
        out = codecs.open(output_file, 'w', 'utf-8')
        with codecs.open(sample_file, 'r', 'utf-8') as f:
            for line in f:
                cols = re.split('\t',line)
                if cols[1] != 'r':
                    continue
                last_field = cols[-1][0:-1]  # take the last value, then strip out the newline.
                fields = re.split(',',last_field)
                if preprocess_function:
                    fields = set(preprocess_function(fields))
                if len(fields.intersection(embeddings)) > 0:
                    out.write(line)
        out.close()

# path='/home/mayankkejriwal/Downloads/memex-cp4-october/'
# SampleFilePreprocessors.filter_r_lines(path+'100-sampled-eyeColor-vals.txt',
#                             path+'unigram-embeddings-10000docs.json', path+'filtered-eyeColor.txt')