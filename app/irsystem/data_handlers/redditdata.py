import json
from app.irsystem.models.helpers import *
import os

class RedditData():
    def __init__(self):
        '''
        self.FOLDER_NAME: folder where all reddit related json data is stored
        self.DATA_ROOT: Path to self.FOLDER_NAME
        self.STATIC_DATA_PATH: Entire path including where self.FOLDER_NAME is
        self.reddit_dict: Dict of reddit results indexed on reddit id
        self.ids_reddit_pair: Tuple of lists as identified in getCleanReddit(), utilized in tfidf
        '''
        self.FOLDER_NAME = 'reddit_data'
        self.DATA_ROOT = os.path.realpath(os.path.dirname('app/data/' + self.FOLDER_NAME))
        self.STATIC_DATA_PATH = os.listdir(os.path.join(self.DATA_ROOT, self.FOLDER_NAME))
        self.reddit_dict = self.getRedditDict()
        self.ids_reddit_pair = self.getCleanReddit()

    def getCleanReddit(self):
        '''
        Preprocesses reddit results to extract and concat reddit titles and body

        Parameters:
            self.reddit_dict:
            {
                id: ('reddit title', 'description', 'id', 'url'),
                ...
            }
        Returns:
            tuple of lists, where the first element is a list of reddit IDs and
            the second element is an array where each element is the corresponding text
            (title and body text concatenated together) for that reddit result.
        '''
        ret = ([], [])
        for key in self.reddit_dict:
            post = self.reddit_dict[key]
            text_str = cleanText(removeHTML(post[0] + ' ' + post[1]))
            ret[0].append(key)
            ret[1].append(text_str)
        return ret

    def getRedditDictFromFile(self):
        '''
        This function returns a dict of reddit information after scanning
        where the reddit data json is located (static jsons must be created first):
        {
            id: ('reddit title', 'description', 'id', 'url', 'created_utc'),
            ...
        }
        '''
        ret = {}
        for filename in self.STATIC_DATA_PATH:
            reddit_file_path = os.path.join(self.DATA_ROOT, self.FOLDER_NAME, filename)
            reddit_file = json.load(open(reddit_file_path))
            for k, submission in enumerate(reddit_file):
                if 'selftext' not in submission:
                    continue
                whole_text = submission['title'] + ' ' + submission['selftext']
                if self.granularClean(whole_text):
                    str_id = str(submission['id'])
                    ret[str_id] = ((submission['title'],
                        submission['selftext'],
                        str_id,
                        submission['full_link'],
                        submission['created_utc']))
        return ret

    def granularClean(self, whole_text):
        bad_list = [
            'grade',
            'gpa',
            'g.p.a',
            'class',
            ' cs ',
            'computer science',
            'engineering',
            'arts',
            'sciences',
            'physics',
            'homework',
            'assignment',
            'math',
            'project',
            'professor',
            'teacher',
        ]
        for w in bad_list:
            if w in whole_text.lower():
                return False
        return True

    def getRedditDict(self):
        '''
        Middle-man function that returns the correct reddit dict
        '''
        return self.getRedditDictFromFile()
