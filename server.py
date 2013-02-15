import tornado.ioloop
import tornado.web
import subprocess
import json
import tempfile
import os
import shlex
from nltk.tokenize import word_tokenize, line_tokenize

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        text = "@Jessica_Chobot did you see the yakuza vs zombies....smh but cool at the same time\nPlease enter the desired filename"
        print ('TemporaryFile:')
        filename = '/tmp/guess_my_name.%s.tmp' % os.getpid()
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
        self.write(output)
        lines = str(output).split('\\n')
        print(lines)
        print (len(lines))
        for line in lines[:-1]:
                tokens = word_tokenize(line)
                print (tokens)
        os.remove(filename)

application = tornado.web.Application([
    (r"/", MainHandler),
])

if __name__ == "__main__":
    application.listen(8889)
    tornado.ioloop.IOLoop.instance().start()