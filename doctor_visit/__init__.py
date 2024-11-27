from otree.api import *
from datetime import datetime, timedelta

doc = """
Симуляция посещения врача: игра, моделирующая выбор времени посещения врача игроками
для минимизации времени ожидания и максимизации награды.
"""

class C(BaseConstants):
    NAME_IN_URL = 'doctor_visit'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 2  # Играем 5 раундов
    APPOINTMENT_DURATION = 30  # минуты
    BASE_REWARD = 700
    PENALTY_PER_MINUTE = 1

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    def calculate_waiting_times(self):
        players = self.get_players()
        # Сортировка игроков по времени прихода
        sorted_players = sorted(players, key=lambda x: self.str_to_minutes(x.arrival_time))
        
        opening_time = 600  # 10:00 в минутах
        closing_time = opening_time + (len(players) * C.APPOINTMENT_DURATION)
        current_time = opening_time
        
        # Сохраняем порядок в очереди и время приема для каждого игрока
        for i, player in enumerate(sorted_players, 1):
            player.queue_position = i
            arrival_minutes = self.str_to_minutes(player.arrival_time)
            
            # Если пришел до открытия
            if arrival_minutes < opening_time:
                waiting_time = opening_time - arrival_minutes
                start_time = opening_time
            else:
                waiting_time = max(0, current_time - arrival_minutes)
                start_time = max(arrival_minutes, current_time)
            
            # Проверка, успевает ли на прием
            # Пациент успевает, если его прием начинается до закрытия
            if start_time < closing_time:
                player.waiting_time = waiting_time
                player.is_complete = True
                player.prize = C.BASE_REWARD - waiting_time * C.PENALTY_PER_MINUTE
                player.appointment_time = self.minutes_to_str(start_time)
                current_time = start_time + C.APPOINTMENT_DURATION
            else:
                player.waiting_time = 0
                player.is_complete = False
                player.prize = 0
                player.appointment_time = "Не попал на прием"
            
            # Сохраняем результаты раунда
            player.participant.vars.setdefault('game_history', []).append({
                'round': self.round_number,
                'arrival_time': player.arrival_time,
                'waiting_time': player.waiting_time,
                'appointment_time': player.appointment_time,
                'prize': player.prize,
                'is_complete': player.is_complete,
                'queue_position': player.queue_position
            })

    @staticmethod
    def str_to_minutes(time_str):
        try:
            # Разбиваем строку на часы и минуты
            hours, minutes = time_str.split(':')
            
            # Преобразуем в числа
            hours = int(hours)
            minutes = int(minutes)
            
            # Проверяем диапазоны
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError("Invalid time format")
            
            return hours * 60 + minutes
            
        except (ValueError, AttributeError):
            raise ValueError(f"Неверный формат времени: {time_str}. Используйте формат ЧЧ:ММ")

    @staticmethod
    def minutes_to_str(minutes):
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"

class Player(BasePlayer):
    # Поля для текущего раунда
    arrival_time = models.StringField(
        label="Выберите время прихода (ЧЧ:ММ)",
        blank=False
    )
    waiting_time = models.IntegerField(initial=0)
    is_complete = models.BooleanField(initial=False)
    prize = models.IntegerField(initial=0)
    queue_position = models.IntegerField(initial=0)
    appointment_time = models.StringField(initial="")

    # Поля для итоговой статистики (заполняются только в последнем раунде)
    total_prize = models.IntegerField(initial=0)
    avg_waiting_time = models.FloatField(initial=0)
    success_rate = models.FloatField(initial=0)
    
    def arrival_time_error_message(self, value):
        # Проверяем формат
        if ':' not in value:
            return 'Используйте формат ЧЧ:ММ, например: 09:30 или 14:15'
        
        try:
            # Разбиваем строку на часы и минуты
            hours, minutes = value.split(':')
            
            # Проверяем, что часы и минуты - числа
            if not hours.isdigit() or not minutes.isdigit():
                return 'Часы и минуты должны быть числами'
            
            # Преобразуем в числа
            hours = int(hours)
            minutes = int(minutes)
            
            # Проверяем диапазоны
            if not (0 <= hours <= 23):
                return 'Часы должны быть от 00 до 23'
            if not (0 <= minutes <= 59):
                return 'Минуты должны быть от 00 до 59'
            
            # Форматируем время в правильный фрмат
            self.arrival_time = f"{hours:02d}:{minutes:02d}"
            
        except ValueError:
            return 'Пожалуйста, введите время в формате ЧЧ:ММ, например: 09:30 или 14:15'
        
        return None

    def custom_export(player):
        # Этот метод определяет, какие данные будут экспортированы
        if player.round_number == C.NUM_ROUNDS:
            return {
                'participant_id': player.participant.id_in_session,
                'total_prize': player.total_prize,
                'avg_waiting_time': player.avg_waiting_time,
                'success_rate': player.success_rate
            }
        return {
            'participant_id': player.participant.id_in_session,
            'round_number': player.round_number,
            'arrival_time': player.arrival_time,
            'waiting_time': player.waiting_time,
            'queue_position': player.queue_position,
            'appointment_time': player.appointment_time,
            'is_complete': player.is_complete,
            'prize': player.prize
        }

class Introduction(Page):
    def vars_for_template(self):
        return {
            'num_players': len(self.subsession.get_players()),
            'closing_time': f"{10 + len(self.subsession.get_players())//2}:00",
            'round_number': self.round_number,
            'total_rounds': C.NUM_ROUNDS
        }

class ArrivalTimeInput(Page):
    form_model = 'player'
    form_fields = ['arrival_time']

    def vars_for_template(self):
        return {
            'round_number': self.round_number,
            'total_rounds': C.NUM_ROUNDS
        }

class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        self.group.calculate_waiting_times()

class Results(Page):
    def vars_for_template(self):
        # Получаем всех игроков, отсортированных по позиции в очереди
        all_players = sorted(self.group.get_players(), key=lambda p: p.queue_position)
        queue_info = []
        
        for player in all_players:
            queue_info.append({
                'id': player.id_in_group,
                'arrival_time': player.arrival_time,
                'queue_position': player.queue_position,
                'waiting_time': player.waiting_time,
                'appointment_time': player.appointment_time,
                'prize': player.prize,
                'is_complete': player.is_complete,
            })
        
        return {
            'queue_info': queue_info,
            'player_id': self.id_in_group,
            'waiting_time': self.waiting_time,
            'is_complete': self.is_complete,
            'prize': self.prize,
            'arrival_time': self.arrival_time,
            'appointment_time': self.appointment_time,
            'queue_position': self.queue_position,
            'round_number': self.round_number,
            'total_rounds': C.NUM_ROUNDS
        }

class FinalResults(Page):
    def is_displayed(self):
        return self.round_number == C.NUM_ROUNDS

    def before_next_page(self, timeout_happened):
        # Сохраняем итоговую статистику в базу данных
        game_history = self.participant.vars.get('game_history', [])
        self.total_prize = sum(round_data['prize'] for round_data in game_history)
        self.avg_waiting_time = sum(round_data['waiting_time'] for round_data in game_history) / len(game_history)
        self.success_rate = sum(1 for round_data in game_history if round_data['is_complete']) / len(game_history) * 100

    def vars_for_template(self):
        game_history = self.participant.vars.get('game_history', [])
        total_prize = sum(round_data['prize'] for round_data in game_history)
        avg_waiting_time = sum(round_data['waiting_time'] for round_data in game_history) / len(game_history)
        success_rate = sum(1 for round_data in game_history if round_data['is_complete']) / len(game_history) * 100

        return {
            'game_history': game_history,
            'total_prize': total_prize,
            'avg_waiting_time': round(avg_waiting_time, 1),
            'success_rate': round(success_rate, 1)
        }

page_sequence = [Introduction, ArrivalTimeInput, ResultsWaitPage, Results, FinalResults]
