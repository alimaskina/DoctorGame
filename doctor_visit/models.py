from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random
from datetime import datetime, timedelta

class Constants(BaseConstants):
    name_in_url = 'doctor_visit'
    players_per_group = None
    num_rounds = 1
    appointment_duration = 30  # минуты
    base_reward = 700
    penalty_per_minute = 1

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    def calculate_waiting_times(self):
        players = self.get_players()
        # Сортировка игроков по времени прихода
        sorted_players = sorted(players, key=lambda x: self.str_to_minutes(x.arrival_time))
        
        opening_time = 600  # 10:00 в минутах
        closing_time = opening_time + (len(players) * Constants.appointment_duration)
        current_time = opening_time
        
        for player in sorted_players:
            arrival_minutes = self.str_to_minutes(player.arrival_time)
            
            # Если пришел до открытия
            if arrival_minutes < opening_time:
                waiting_time = opening_time - arrival_minutes
                start_time = opening_time
            else:
                waiting_time = max(0, current_time - arrival_minutes)
                start_time = max(arrival_minutes, current_time)
            
            print(player, start_time, current_time, closing_time)
            
            # Проверка, успевает ли на прием
            if start_time <= closing_time:
                player.waiting_time = waiting_time
                player.is_complete = True
                player.prize = Constants.base_reward - waiting_time * Constants.penalty_per_minute
                current_time = start_time + Constants.appointment_duration
            else:
                player.waiting_time = 0
                player.is_complete = False
                player.prize = 0

    @staticmethod
    def str_to_minutes(time_str):
        time_obj = datetime.strptime(time_str, '%H:%M')
        return time_obj.hour * 60 + time_obj.minute

class Player(BasePlayer):
    arrival_time = models.StringField(
        label="Выберите время прихода (ЧЧ:ММ)",
        blank=False
    )
    waiting_time = models.IntegerField(initial=0)
    is_complete = models.BooleanField(initial=False)
    prize = models.IntegerField(initial=0)

    def arrival_time_error_message(self, value):
        try:
            time_obj = datetime.strptime(value, '%H:%M')
            if not (0 <= time_obj.hour < 24 and 0 <= time_obj.minute < 60):
                return 'Пожалуйста, введите корректное время в формате ЧЧ:ММ'
        except ValueError:
            return 'Пожалуйста, введите время в формате ЧЧ:ММ' 