from django.core.management.base import BaseCommand
from tom_alerts.models import BrokerQuery
from tom_alerts.alerts import get_service_class, get_service_classes
from datetime import datetime 

class Command(BaseCommand):
    help = "run an alert query"

    def add_arguments(self, parser):
       parser.add_argument('--query_name', help='indicates name of query to run') 
       #Django doc. -> how parser works: https://docs.djangoproject.com/en/2.2/howto/custom-management-commands/

    def handle(self, *args, **options):
        query = BrokerQuery.objects.get(name=options['query_name'])
        broker_class = get_service_class(query.broker)()
        alerts = broker_class.fetch_alerts(query.parameters_as_dict)

        for alert in alerts:
            now = datetime.now()
            #print()
            print(now, alert, '\n')
            alert = broker_class.fetch_alert(alert['lco_id'])
            target = broker_class.to_target(alert)
            #broker_class.process_reduced_data(target, alert)
            target.save()

