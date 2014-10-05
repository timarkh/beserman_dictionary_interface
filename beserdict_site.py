import time
from lxml import etree
from flask import Flask, url_for, request, render_template, redirect, session, jsonify
import codecs, re, uuid

app = Flask(__name__)
app.secret_key = 'k_bXnlu654Q'
sessionData = {}    # session key -> dictionary with the data for current session
dictTree = None
lemmas = []

def load_dictionary(fname):
    global dictTree, lemmas
    dictTree = etree.parse(fname)
    lemmaEls = dictTree.xpath(u'/root/Lemma')
    for lemmaEl in lemmaEls:
        lemmaSignEl = lemmaEl.xpath(u'Lemma.LemmaSign')
        if len(lemmaSignEl) != 1:
            continue
        lemma = lemmaSignEl[0].xpath(u'string()')
        if u'[' in unicode(lemma):
            continue
        homonymNumberEl = lemmaEl.xpath(u'Lemma.HomonymNumber')
        if len(homonymNumberEl) == 1:
            lemma += u' (' + homonymNumberEl[0].xpath(u'string()') + u')'
        #print unicode(lemma)
        lemmas.append(unicode(lemma))


def initialize_session():
    global sessionData
    session[u'session_id'] = str(uuid.uuid4())
    sessionData[session[u'session_id']] = {}

    
def get_session_data(fieldName):
    global sessionData
    try:
        dictCurData = sessionData[session[u'session_id']]
        requestedValue = dictCurData[fieldName]
        return requestedValue
    except:
        return None


def set_session_data(fieldName, value):
    global sessionData
    if u'session_id' not in session:
        initialize_session()
    sessionData[session[u'session_id']][fieldName] = value


def in_session(fieldName):
    global sessionData
    if u'session_id' not in session:
        return False
    return fieldName in sessionData[session[u'session_id']]


def find_element(lemma):
    global dictTree
    homonymNum = 0
    m = re.search(u'^(.+) \\(([0-9]+)\\)$', lemma, flags=re.U)
    if m != None:
        lemma = m.group(1)
        homonymNum = int(m.group(2))
    try:
        if homonymNum <= 0:
            entryEl = dictTree.xpath(u'/root/Lemma[Lemma.LemmaSign/text()=\'' +
                                     lemma + u'\']')[0]
        else:
            entryEl = dictTree.xpath(u'/root/Lemma[Lemma.LemmaSign/text()=\'' +
                                     lemma +
                                     u'\' and Lemma.HomonymNumber/text()=\'' +
                                     str(homonymNum) + u'\']')[0]
    except:
        return None
    return entryEl


@app.route('/')
def index():
    global lemmas
    return render_template(u'index.html', lemmas=lemmas)


@app.route('/_get_entry')
def get_entry():
    lemma = request.args.get('lemma', u'', type=unicode).replace(u"'", u'')
    entryEl = find_element(lemma)
    if entryEl is None:
        return jsonify(entryHtml=u'nonono')
    lemmaSignEl = entryEl.xpath(u'Lemma.LemmaSign')
    lemmaSign = unicode(lemmaSignEl[0].xpath(u'string()'))
    
    homonymNumber = None
    homonymNumberEl = entryEl.xpath(u'Lemma.HomonymNumber')
    if len(homonymNumberEl) == 1:
        homonymNumber = unicode(homonymNumberEl[0].xpath(u'string()'))

    psBlocks = []
    psBlockEls = entryEl.xpath(u'PSBlock')
    for psBlockEl in psBlockEls:
        psBlock = {u'psbPS': u'?', u'values': []}
        psBlocks.append(psBlock)
        posEl = psBlockEl.xpath(u'PSBlock.PsbPS')
        if len(posEl) == 1:
            psBlock[u'psbPS'] = unicode(posEl[0].xpath(u'string()'))
        valueEls = psBlockEl.xpath(u'Value')
        for valueEl in valueEls:
            value = {u'valTr': u'', u'examples': []}
            valTrEl = valueEl.xpath(u'Value.ValTr')
            if len(valTrEl) == 1:
                value[u'valTr'] = unicode(valTrEl[0].xpath(u'string()'))
            psBlock[u'values'].append(value)
    entry = render_template(u'entry.html', lemmaSign=lemmaSign,
                            homonymNumber=homonymNumber,
                            psBlocks=psBlocks)
    
    return jsonify(entryHtml=entry)


def start_server():
    load_dictionary(u'dict.xml')
    app.run(host='0.0.0.0', port=2019)
    #app.config['SERVER_NAME'] = '62.64.12.18:5000'
   
if __name__ == u'__main__':
    start_server()
