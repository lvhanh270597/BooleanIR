from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import word_tokenize
from math import log
import os

class Stack:
    def __init__(self):
        self.words = []
    def top(self):
        if len(self.words) == 0: 
            return None
        return self.words[-1]
    def pop(self):
        if len(self.words) == 0:
            return 
        self.words.pop()
    def push(self, word):
        self.words.append(word)
    def size(self):
        return len(self.words)
    def empty(self):
        return len(self.words) == 0
    
class Document:
    def __init__(self, title = None, content = None, words = None):
        self.title = title
        self.content = content
        self.words = words[:]
    
    def exist(self, word):
        return self.words.count(word) > 0
    
    def __str__(self):
        return "######################[title: %s]#####################\ncontent: %s" %(self.title, self.content)
        
        
def read_data(folder, fileName):
    stemmer = SnowballStemmer("english")
    content = open(folder + '/' + fileName).read()
    
    words = word_tokenize(content)
    words = [word for word in words if word not in stopwords.words('english')]
    words = [stemmer.stem(word) for word in words] 
    document = Document(fileName, content, words)
    return (document, set(words))
    
def read_data_from_a_folder(folder):
    documents = []
    vocab = set()

    for name in os.listdir(folder):
        document, words = read_data(folder, name)
        documents += [document]
        vocab = vocab.union(words)
        
    return (documents, list(vocab))
        
def build_matrix(vocabulary, documents):
    matrix = {}
    for term in vocabulary:
        matrix[term] = [doc.exist(term) for doc in documents]
    return matrix

def convert_to_suffixNotion(query):
    operators = ['__or__', '__and__', '__not__', '(', ')']
    priority = {        
        '(' : -1,
        '__not__' : 2,
        '__and__' : 1,
        '__or__'  : 0,
    }
    
    words = query    
    suffix = []
    stack = Stack()
    
    for word in words:
        if (word == '('):
            stack.push(word)
        else:
            if (word == ')'):
                top = stack.top()
                if (top == None):
                    print("Error convert to suffix")
                    return (None, None)

                while (top != '('):
                    suffix.append(stack.top())
                    stack.pop()
                    if stack.empty(): break
                    top = stack.top()
                stack.pop()
            else:            
                if (word not in priority.keys()):
                    suffix.append(word)
                else:
                    top = stack.top()
                    if (top == None):
                        stack.push(word)
                    else:
                        while (not stack.empty()):                                            
                            
                            if (top == '(') or (priority[top] < priority[word]):
                                break
                                
                            suffix.append(top)
                            stack.pop()                        
                            if stack.empty(): break
                            top = stack.top()
                        stack.push(word)
    
    while (stack.empty() == False):
        suffix.append(stack.top())
        stack.pop()
        
    variables = [word for word in words if word not in operators]
    return (suffix, list(set(variables)))
        
def evaluate(function):
    operators = ['__or__', '__and__', '__not__']
    
    if (len(function) == 0): return None
    
    stack = Stack()
    for word in function:
        if (word not in operators):
            stack.push(bool(int(word)))
        else:
            if (word == '__not__'):
                top = stack.top()
                stack.pop()
                stack.push(not(top))
            else:
                if (word == '__and__'):
                    u = stack.top()
                    stack.pop()
                    v = stack.top()
                    stack.pop()
                    stack.push(u and v)
                else:
                    if (word == '__or__'):
                        u = stack.top()
                        stack.pop()
                        v = stack.top()
                        stack.pop()
                        stack.push(u or v)
    
    if (stack.size() != 1):
        print('Can not evaluate this function')
        return None
    
    return stack.top()

def test_function(function, variables, number = 0):    
    value = {}
    sentence = ' '.join(function)
    
    for i in range(len(variables)):
        var = variables[i]
        bitwise = (number >> i) & 1
        value[var] = bitwise
        sentence = sentence.replace(var, str(bitwise))
        
    function = sentence.split()
    
    if (evaluate(function)):
        return value
    return None

def analyze_and_encode(vocabulary, query):
    operators = ['__or__', '__and__', '__not__', '(', ')']
    stemmer = SnowballStemmer("english")
    query = word_tokenize(query)

    query = [word for word in query if word not in stopwords.words('english')]
    
    new_query = []
    for word in query:
        word = stemmer.stem(word)
        if (word in operators) or (word in vocabulary):
            new_query.append(word)
    query = new_query
    '''
        analyze the binary vectors which have true with query
        return binary vectors which represents A^-B^C^D^-E:
        {
        A : True
        B : False
        C : False
        ...
        }
    '''
    binary_queries = []    
    suffix_notion, variables = convert_to_suffixNotion(query)    
    if (suffix_notion == None): return None
    
    for number in range(0, 1 << len(variables)):
        test_value = test_function(suffix_notion[:], variables[:], number)
        if (test_value != None):
            binary_queries.append(test_value)
    return binary_queries
    
def invert(L):
    return [not e for e in L]
def andList(L1, L2):
    if L1 == None: return L2
    if L2 == None: return L1
    return [(l1 and l2) for (l1, l2) in zip(L1, L2)]

def showResult(result, documents):
    for i in range(len(result)):
        if (result[i]):
            print(documents[i])
            print('-------------------------------------')

def search(binary_queries, matrix_term_doc, documents):   
    if (binary_queries == None) or len(binary_queries) == 0:
        print("No result")
        return 
    
    for query in binary_queries:
        result = None
        for word in query.keys():
            val = query[word]
            L = matrix_term_doc[word]
            if (not val): L = invert(L)
            result = andList(result, L)
        showResult(result, documents)
    
def main():    
    
    #system
    documents, vocabulary = read_data_from_a_folder('data')
    
    matrix_term_doc = build_matrix(vocabulary, documents)
   
    #user
    query = input("Enter your boolean query: ")
    
    binary_queries = analyze_and_encode(vocabulary, query)
    
    #searching
    results = search(binary_queries, matrix_term_doc, documents)
    
main()
