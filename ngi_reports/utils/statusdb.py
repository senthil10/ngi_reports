#!/usr/bin/env python

import couchdb
import os
import yaml

from datetime import datetime

class statusdb_connection(object):
    """Main class to make connection to the statusdb, by default looks for config
    file in home, if not try with provided config
    
    :param dict config: a dictionary with essential info to make a connection
    :param logger log: a logger instance to log information when neccesary
    """
    def __init__(self, config=None, log=None):
        self.log = log
        default_config = os.path.join(os.environ.get("HOME"), ".ngi_config", "statusdb.yaml")
        # if there is no first default config, try to get it from environ 
        if not os.path.exists(default_config):
            default_config = os.path.join(os.environ.get("STATUS_DB_CONFIG"))
        try:
            with open(default_config) as f:
                conf = yaml.load(f)
                config = conf["statusdb"]
        except IOError:
            if not config:
                raise SystemExit("Could not find any config info in '~/.ngi_config/statusdb.yaml' or ENV variable 'STATUS_DB_CONFIG'")

        self.user = config.get("username")
        self.pwrd = config.get("password")
        self.port = config.get("port")
        self.url = config.get("url")
        self.url_string = "http://{}:{}@{}:{}".format(self.user, self.pwrd, self.url, self.port)
        self.display_url_string = "http://{}:{}@{}:{}".format(self.user, "*********", self.url, self.port)
        self.connection = couchdb.Server(url=self.url_string)        
        if not self.connection:
            raise SystemExit("Connection failed for url {}, also check the information in config".format(self.display_url_string))
    
    def get_entry(self, name, use_id_view=False):
        """Retrieve entry from given db for a given name.
        
        :param name: unique name identifier (primary key, not the uuid)
        :param db: name of db to fetch data from
        """
        if use_id_view:
            view = self.id_view
        else:
            view = self.name_view
        if not view.get(name, None):
            if self.log:
                self.log.warn("no entry '{}' in {}".format(name, self.db))
            return None
        return self.db.get(view.get(name))
    
    def get_project_flowcell(self, project_id, open_date="2015-01-01", date_format="%Y-%m-%d"):
        """From information available in flowcell db connection collect the flowcell this project was sequenced
        
        :param project_id: NGI project ID to get the flowcells
        :param open_date: Open date of project to skip the check for all flowcells
        :param date_format: The format of specified open_date
        """
        try:
            open_date = datetime.strptime(open_date, date_format)
        except:
            open_date = datetime.strptime("2015-01-01", "%Y-%m-%d")
        
        project_flowcells = {}
        date_sorted_fcs = sorted(self.proj_list.keys(), key=lambda k: datetime.strptime(k.split('_')[0], "%y%m%d"), reverse=True)
        for fc in date_sorted_fcs:
            fc_date, fc_name = fc.split('_')
            if datetime.strptime(fc_date,'%y%m%d') < open_date:
                break
            if project_id in self.proj_list[fc] and fc_name not in project_flowcells.keys():
                project_flowcells[fc_name] = {'name':fc_name,'run_name':fc, 'date':fc_date, 'db':self.db.name}
        
        return project_flowcells

class ProjectSummaryConnection(statusdb_connection):
    def __init__(self, dbname="projects"):
        super(ProjectSummaryConnection, self).__init__()
        self.db = self.connection[dbname]
        self.name_view = {k.key:k.id for k in self.db.view("project/project_name", reduce=False)}
        self.id_view = {k.key:k.id for k in self.db.view("project/project_id", reduce=False)}

class SampleRunMetricsConnection(statusdb_connection):
    def __init__(self, dbname="samples"):
        super(SampleRunMetricsConnection, self).__init__()
        self.db = self.connection[dbname]

class FlowcellRunMetricsConnection(statusdb_connection):
    def __init__(self, dbname="flowcells"):
        super(FlowcellRunMetricsConnection, self).__init__()
        self.db = self.connection[dbname]
        self.name_view = {k.key:k.id for k in self.db.view("names/name", reduce=False)}
        self.proj_list = {k.key:k.value for k in self.db.view("names/project_ids_list", reduce=False) if k.key}

class X_FlowcellRunMetricsConnection(statusdb_connection):
    def __init__(self, dbname="x_flowcells"):
        super(X_FlowcellRunMetricsConnection, self).__init__()
        self.db = self.connection[dbname]
        self.name_view = {k.key:k.id for k in self.db.view("names/name", reduce=False)}
        self.proj_list = {k.key:k.value for k in self.db.view("names/project_ids_list", reduce=False) if k.key} 
