from pymongo import MongoClient
import math
import time

class CalculateTopApp(object):
    db_name = 'app_store'
    app_info_coll_name = 'app_info'
    user_download_history_coll_name = 'user_download_history'

    client = None
    db = None
    app_info_coll = None
    user_download_history_coll = None
    appids = None
    download_historys = None

    def __init__(self):
        '''
        Initialize MangoDB client, database and collection object
        '''
        self.client = MongoClient()
        self.db = self.client[self.db_name]
        self.app_info_coll = self.db[self.app_info_coll_name]
        self.user_download_history_coll = \
                self.db[self.user_download_history_coll_name]

    def get_all_appids(self):
        '''
        Save all appid in a set.
        '''
        self.appids = set()
        for app in self.app_info_coll.find():
            self.appids.add(app['app_id'])

    def get_all_download_historys(self):
        '''
        Save all download history in a list.
        '''
        self.download_historys = []
        for download_history in self.user_download_history_coll.find():
            self.download_historys.append(download_history['download_history'])

    def calculate_top_n_app(self, n):
        '''
        Calculate top n app recommendation. So that, given an appid, we can
        get n most relative appid.
        '''
        #self.get_all_appids()
        self.get_all_download_historys()
        self.calculate_all_app_relation()

        for app in self.app_relation:
            relation_list = self.get_recommend_app_list(app)
            self.populate_top_n_app_mongodb(app, relation_list, n)

    def calculate_all_app_relation(self):
        '''
        Calculate all relation parameter

        We define relation parameter between app a1 and app a2 as summation of
        all cosine similarity value of download history which contains both
        app a1 and a2.
        Cosine similarity value of download history is 
        1 / sqrt(len(download history)) to both app a1 and app a2.
        E.g. download history {a1, a2, a5, a8} results in a relation parameter
        between app a1 and app a2 of 1 / sqrt(4) --> 0.5.

        How to calculate:
        1.Traverse all download history
        2.Calculate relation parameter by 1 / sqrt(len(download history))
        3.Add this parameter to all apps in download history

        Time Complexity: O(number of user * (longest download history) ^ 2)
        Space Complexity: O((number of apps) ^ 2)
        '''
        self.app_relation = {}
        for download_history in self.download_historys:
            length = len(download_history)
            para = 1.0 / math.sqrt(length)
            for i in xrange(0, length):
                for j in xrange(i + 1, length):
                    app_i = download_history[i]
                    app_j = download_history[j]
                    self.add_relation(self.app_relation, app_i, app_j, para)
                    self.add_relation(self.app_relation, app_j, app_i, para)

    def calculate_two_app_relation(self, app1, app2):
        '''
        Like calculate all app relation, but we simply skip download_history
        that does not contain either app1 or app2
        '''
        self.get_all_download_historys()

        self.app_relation = {}
        para = 0.0
        for download_history in self.download_historys:
            if app1 not in download_history or app2 not in download_history:
                continue
            length = len(download_history)
            para += 1.0 / math.sqrt(length)
        return para

    def calculate_user_top_n_recommend_app_list(self, user_id, n):
        '''
        Calculate recommend app list for each user based on user's download 
        history.
        '''
        user_recommend_app_list = self.calculate_user_recommend_app_list(user_id)
        return user_recommend_app_list[:n]

    def calculate_user_recommend_app_list(self, user_id):
        '''
        Get total recommend app list based on user's download history
        '''
        #prepare app relation parameter and download history
        self.get_all_download_historys()
        download_history = self.user_download_history_coll\
                .find({"user_id" : user_id})[0]['download_history']
        self.calculate_all_app_relation()

        return self.calculate_recommend_app_list(download_history, self.app_relation)

    def calculate_recommend_app_list(self, src_list, app_relation):
        '''
        Based on src_list and app relation, calculate recommend app list
        '''
        #get recommend app dict
        recommend_app_dict = {}
        for app in src_list:
            for recommend_app in app_relation[app]:
                #if already has, doesn't recommend
                if recommend_app in src_list:
                    continue
                #save relation parameter
                para = app_relation[app][recommend_app]
                if recommend_app in recommend_app_dict:
                    recommend_app_dict[recommend_app] += para
                else:
                    recommend_app_dict[recommend_app] = para

        #get sorted recommend app list
        recommend_app_list = []
        for app in recommend_app_dict:
            recommend_app_list.append([app, recommend_app_dict[app]])
        recommend_app_list.sort(key = lambda x : x[1], reverse = True)

        return recommend_app_list

    def show_user_top_n_recommend_app_list(self, user_id, n):
        '''
        Print recommend app list for each user in unicode.
        '''
        user_top_n_recommend_app_list = \
                self.calculate_user_top_n_recommend_app_list(user_id, n)
        download_history = self.user_download_history_coll\
                .find({"user_id" : user_id})[0]['download_history']

        print "user has following apps:"
        for app in download_history:
            print self.find_app_name_by_id(app)
        print "we recommend following apps:"
        for app in user_top_n_recommend_app_list:
            print self.find_app_name_by_id(app[0])

    def find_app_name_by_id(self, app_id):
        return self.app_info_coll.find({"app_id" : app_id})[0]["title"].encode("utf-8")

    def get_recommend_app_list(self, app):
        '''
        Sort (in descending order) and get app recommendation list.
        '''
        relation_list = []
        for relative_app in self.app_relation[app]:
            para = self.app_relation[app][relative_app]
            relation_list.append([relative_app, para])
        relation_list.sort(key = lambda x : x[1], reverse = True)
        return relation_list

    def populate_top_n_app_mongodb(self, app, relation_list, n):
        '''
        Populate top n appid into MongoDB
        '''
        top_list = []
        for i in range(0, n):
            top_list.append(relation_list[i][0])
        self.app_info_coll.update_one(\
                {"app_id" : app},\
                {"$set" : {"recommend" : top_list}})

    def add_relation(self, app_relation, app_i, app_j, para):
        '''
        Add relation parameter from app_j to app_i.
        '''
        if app_i not in app_relation:
            app_relation[app_i] = {}
        if app_j not in app_relation[app_i]:
            app_relation[app_i][app_j] = para
        else:
            app_relation[app_i][app_j] += para

if __name__ == "__main__":
    start = time.clock()
    c = CalculateTopApp()
    #print c.calculate_user_top_n_recommend_app_list(3,5)
    c.calculate_top_n_app(5)
    end = time.clock()
    print end - start
