"""
This file contains code related to arch use conventions.

The hope is that the core databse extractor will can remain stable as use conventions
evolve.

An example a use convention is "always  model a service dependency through an
Application Component of type "interface".
"""

import argparse
import sqlite3
import shlog
import tabulate


######################################################
#
#  HACK -- copied this  -- need more code factoring.
#
########################################################

def q(args, sql):
    #a funnel routned for report queries, main benefit is query printing
    con = sqlite3.connect(args.dbfile)
    con.text_factory = lambda x: x.decode("utf-8")
    cur = con.cursor()
    shlog.verbose (sql)
    result  = cur.execute (sql)
    con.commit()
    return result


######################################################
#
#  Build supporting DB tables.
#  
########################################################

def mkTables(args):
    "Build tables at ingest time"
    
    mk_requirements(args)
    mkserving(args) 
    
def mkserving(args):
    """
    Build a table, SERVING, that compiles the relationship of one application component
    providing servince to another  application component. Thsi table Hides the fact
    that in the modeling tool this relationship is expressed though an application

    interface component.  The SERVING TABLE will allow a recursive query discovering
    the chain of service dependencies.
    """

    # ok I know this seems baroque. It too some time for a newbie to figure this
    # large Join out, since it is a join of joins. composing the query from other
    # Query strings lets me debug all this join-by-join. 
    
    #Get the Application components that are served by an interface
    served = """
    select R1.target, R1.source, E1.name,  E1.id  
               from relations R1
            JOIN 
                Elements E1 on R1.Target = E1.ID
            where E1.type = 'ApplicationComponent'
              and R1.type = 'ServingRelationship'

    """
    #get the application components that provide the interface
    providing_service = """
    select R2.Target, R2.Source, E2.name,  E2.id 
               from relations R2
            JOIN 
                Elements E2 on R2.Source = E2.ID
            where E2.type = 'ApplicationComponent'
              and R2.type = 'CompositionRelationship'
     """

    sql = """  CREATE TABLE
                  Serving AS
               SELECT
                   R1.name  Served_Name,
                   R1.id    Served_ID,
                   R2.name  Serving_name,
                   R2.id    Serving_ID
                 FROM
                   (%s) R1
                 JOIN
                   (%s) R2
                 ON R2.target = R1.source 

    """ % (served, providing_service)
    shlog.normal ("Making service associative table ")
    q(args, sql)

def mk_requirements(args):
    """
    Build a table, REQUIREMENTS, that compiles the relationship of one application component
    providing servince to each componet requirement of a master requirement.
    The REQUIREMENTS  provides an asscoaiteve tabel fo master requiremetes an deteiled requiremetns
    """
    # Get the flattened list of requirements,
    # Recording any aggrigating requirement.
    # Reference ID is how an application element or a Nod referes to a requirement
    # Detail_is is the ID that cariies the detailof the requirement.
    # the tabel flattens out  a master requirememtn  "stuff all services do" into  the numerous details all do.
    sql = """
        CREATE TABLE
           requirements AS  
        SELECT
          master.name  Reference_name,
          master.id    Reference_id,
          part.name    Detail_name,
          part.id      Detail_id
        FROM elements part
        JOIN Relations composition ON part.id   = composition.target
        JOIN elements master       ON master.id = composition.source
        AND  master.Type = 'Requirement'
        AND  composition.Type = 'CompositionRelationship'
        AND  part.Type   = 'Requirement'
         """
    q(args,sql)

    #
    # Now go add singletone requiirements.
    # these have no attached compostion relationship
    sql = """
        SELECT
           req.name  Reference_name,
           req.id    Reference_id,
           req.name  Detail_name,
           req.id    Detail_id
        FROM elements req
        WHERE id in
            (SELECT target FROM Relations r where r.type = 'RealizationRelationship') 
         AND req.type = 'Requirement'
    """
    q(args, sql)
    
def parsers(subparsers):
    """
    make any visible command line subcommands from this module
    """ 
    #Subcommand  make an emty archiamte v1 databse.
    #debug_parser = subparsers.add_parser('debug', description=debug.__doc__)
    #debug_parser.set_defaults(func=debug)
    #debug_parser.add_argument("dbfile", help="name of databse file")
