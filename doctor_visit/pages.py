from otree.api import Page, WaitPage
from datetime import datetime, timedelta

class Introduction(Page):
    def vars_for_template(self):
        return {
            'num_players': len(self.subsession.get_players()),
            'closing_time': f"{10 + len(self.subsession.get_players())//2}:00"
        }

class ArrivalTimeInput(Page):
    form_model = 'player'
    form_fields = ['arrival_time']

class ResultsWaitPage(WaitPage):
    after_all_players_arrive = 'calculate_waiting_times'

class Results(Page):
    def vars_for_template(self):
        return {
            'waiting_time': self.player.waiting_time,
            'is_complete': self.player.is_complete,
            'prize': self.player.prize,
        }

page_sequence = [Introduction, ArrivalTimeInput, ResultsWaitPage, Results] 