import uuid, sys, base64
import tornado.ioloop
import tornado.web
from tornado.web import url
import tornado.httpserver
import logging.config
import configparser
from tornado.options import define, options
import subprocess
import ujson
import tempfile
import os
import time
import shlex
from nltk.tokenize import word_tokenize, line_tokenize

define("port", default=8888, type=int)
define("config_file", default="app_config.yml", help="app_config file")

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        #Use %0A (=\n) as URL seperator between tweets   
        text = self.get_argument("tweets", "")
        if text == "":
                self.set_status(404)
                self.write('No input text detected')
                self.finish()
                return
                
        print ('TemporaryFile:')
        millis =  int(round(time.time()*1000))
        filename = '/tmp/guess_my_name.%s.tmp' % millis
        temp = open(filename, 'w+b')
        temp.write(bytes(text, 'UTF-8'))
        try:
                print ('temp:', temp)
                print ('temp.name:', temp.name)
        finally:
        # Automatically cleans up the file
                temp.close()        
        #| python python/ner/extractEntities2.py --classify --pos --event
        command = "cat %s" % filename
        command2 = "python python/ner/extractEntities2.py --classify --pos --chunk"
        args = shlex.split(command)
        args2 = shlex.split(command2)
        p1 = subprocess.Popen(args,stdout=subprocess.PIPE)
        p2 = subprocess.Popen(args2,stdin=p1.stdout,stdout=subprocess.PIPE)
        p1.stdout.close()
        output = p2.communicate()[0]
        original_lines = line_tokenize(text)
        lines = str(output).split('\\n')
        print(lines)
        print (len(lines))
        response = dict()
        
        for line in lines[:-2]:
                index_line = original_lines[lines.index(line)]
                response[original_lines[lines.index(line)]] = dict()
                response[index_line]['nlp'] = line
                tokens = word_tokenize(line)
                #print (tokens)
                chunk = ""
                chunk_id = ""
                for token in tokens:
                      
                      identifiers = list()
                      identifiers = token.split('/')
                      #print (identifiers)
                      
                      if len(identifiers) > 1:
                                if 'B' in identifiers[1]:
                                        print ('Entity!')
                                        print (identifiers[1])
                                        print (identifiers[0])
                                        chunk = identifiers[0]
                                        chunk_id = identifiers[1][2:]
                                        if not chunk_id in response[index_line]:
                                                response[index_line][chunk_id] = set()
                                elif 'I' in identifiers[1]:
                                        chunk += ' %s' % identifiers[0]
                                elif len(chunk) > 0:
                                        response[index_line][chunk_id].add(chunk)
                                        chunk = ""
                                        chunk_id=""
                                else:
                                        chunk = ""
                                        chunk_id = ""
                                        
        os.remove(filename)
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")
        self.write(ujson.dumps(response))
        self.finish()

class Application(tornado.web.Application):
        def __init__(self, **overrides):
                handlers = [
                        url(r'/', MainHandler, name='index')
                ]
                
        #xsrf_cookies is for XSS protection add this to all forms: {{ xsrf_form_html() }}
                settings = {
                'static_path': os.path.join(os.path.dirname(__file__), 'static'),
                'template_path': os.path.join(os.path.dirname(__file__), 'templates'),
                "cookie_secret":    base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
                'xsrf_cookies': False,
                'debug':False,
                'log_file_prefix':"tornado.log",
                }

                tornado.web.Application.__init__(self, handlers, **settings) # debug=True ,        

def main():
        #tornado.options.parse_command_line()
        sockets = tornado.netutil.bind_sockets(options.port)
        if not 'win' in sys.platform:
                tornado.process.fork_processes(8, 0)
        server = tornado.httpserver.HTTPServer(Application())
        server.add_sockets(sockets)	
        tornado.ioloop.IOLoop.instance().start()
        
if __name__ == '__main__':
    main()
    