import logging
import traceback

from flask_restplus import Api

from sqlalchemy.orm.exc import NoResultFound

log = logging.getLogger(__name__)


api = Api(version='1.0', title='C2 API',
          description='Simple Command and Control API for Apache NiFi MiNiFi agents')


@api.errorhandler
def default_error_handler(e):
    message = 'An unhandled exception occurred.'
    log.exception(message)



@api.errorhandler(NoResultFound)
def database_not_found_error_handler(e):
    """No results found in database"""
    log.warning(traceback.format_exc())
    return {'message': 'A database result was required but none was found.'}, 404