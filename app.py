from flask import Flask, request, render_template
import PyPDF2
import docx
import requests
from bs4 import BeautifulSoup
from nltk import sent_tokenize, word_tokenize, pos_tag
from nltk.corpus import stopwords
import re
import spacy

nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)

stop_words = set(stopwords.words('english'))

def clean_text(text):
    # convert to lowercase
    text = text.lower()
    
    # remove line breaks
    text = text.replace('\n', ' ')
    
    # remove punctuation
    text = re.sub(r'[^\w\s]', '', text)
    
    # remove stop words
    words = word_tokenize(text)
    words = [word for word in words if not word in stop_words]
    text = ' '.join(words)
    
    # remove numbers and web links
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'http\S+', '', text)
    
    return text

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        url = request.form['url']
        text = ''

        if file:
            filename = file.filename
            if filename.endswith('.pdf'):
                text = extract_text_from_pdf(file)
            elif filename.endswith('.docx'):
                text = extract_text_from_docx(file)
        elif url:
            text = extract_text_from_website(url)
        emails = find_common_email(text)
        phone = find_phone_numbers(text)
        web_link = find_web_links(text)
        address= find_addresses(text)
        person_name= find_person_names(text)
        dates = find_dates(text)
        text_clean = clean_text(text)
        sentences, words = tokenize_text(text_clean)
        num_sentences, num_words, num_chars = count_text(sentences, words)
        tagged_words = tag_words(words)
        adverbs = extract_pos_words(tagged_words, 'RB')
        nouns = extract_pos_words(tagged_words, 'NN')
        adjectives = extract_pos_words(tagged_words, 'JJ')
       
        
        return render_template('result.html', 
                                num_sentences=num_sentences,
                                num_words=num_words,
                                num_chars=num_chars,
                                adverbs=adverbs,
                                nouns=nouns,
                                adjectives=adjectives,
                                emails=emails,
                                phone= phone,
                                web_link=web_link,
                                address= address,
                                person_name=person_name,
                                dates = dates,
                                text=text,
                                text_clean = text_clean)
    else:
        return render_template('index.html')

def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfFileReader(file)
    text = ''
    for page_num in range(pdf_reader.getNumPages()):
        page = pdf_reader.getPage(page_num)
        text += page.extractText()
    return text

def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = ''
    for para in doc.paragraphs:
        text += para.text
    return text

def extract_text_from_website(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'html.parser')
    text = ''
    for para in soup.find_all('p'):
        text += para.text
    return text

def tokenize_text(text):
    sentences = sent_tokenize(text)
    words = word_tokenize(text)
    return sentences, words

def count_text(sentences, words):
    num_sentences = len(sentences)
    num_words = len(words)
    num_chars = sum(len(word) for word in words)
    return num_sentences, num_words, num_chars

def extract_pos_words(tagged_words, pos):
    return [word for word, tag in tagged_words if tag.startswith(pos)]

def tag_words(words):
    tagged_words = pos_tag(words)
    return tagged_words

def find_string_match(text, keyword):
    match_words = []
    lines = text.split('\n')
    for line in lines:
        if keyword in line:
            match_words.append(line)
    return match_words


    

def find_common_email(text):
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(pattern, text)
    freq = {}
    for email in emails:
        if email in freq:
            freq[email] += 1
        else:
            freq[email] = 1
    return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]

def find_phone_numbers(text):
     # Remove white space
    text = " ".join(text.split())
     # Remove white space and parentheses
    text = text.replace(" ", "").replace("(", "").replace(")", "")
    text = re.sub(r"\s|\(|\)|\-", "", text)

    phone_numbers = re.findall(r"\+\d+", text)
    return [phone_number[1:] for phone_number in phone_numbers]

def find_addresses(text):
    

    addresses = re.compile(r'\d+\s+[a-zA-Z0-9\s.,#-]+[^\d\s]\d{5}')
    addresses = addresses.findall(text)
    return addresses
    

def find_web_links(text):
    # Find web links in format http(s)://www.example.com
    web_links = re.findall(r'http(s)?://[a-zA-Z0-9-]+\.[a-zA-Z]+(/[a-zA-Z0-9-]+)*', text)
    # Find web links in format www.example.com or example.com
    web_links += re.findall(r'www\.[a-zA-Z0-9-]+\.[a-zA-Z]+(/[a-zA-Z0-9-]+)*|[a-zA-Z0-9-]+\.[a-zA-Z]+(/[a-zA-Z0-9-]+)*', text)
    return web_links

def find_person_names(text_clean):
    doc = nlp(text_clean)
    person_names = []
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            person_names.append(ent.text)
    return person_names

def find_dates(text):
    
    pattern = r"\b\d{1,2}(?:st|nd|rd|th)?(?:\s+(?:of\s+)?[a-zA-Z]+)?\s+(?:\d{4}|\d{2}(?:\d{2})?)(?![^\s.,?!])|\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"
    dates = re.findall(pattern, text)
    return dates

def find_word(text, keyword):
    words = text.split()
    freq = {}
    for word in words:
        if keyword in word:
            if word in freq:
                freq[word] += 1
            else:
                freq[word] = 1
    return sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]

if __name__ == '__main__':
    app.run(debug=True)
