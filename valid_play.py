# Includes functions that check whether or not a play is valid

def phazed_is_valid_play(play, player_id, table, turn_history, phase_status, 
                         hand, discard):
    '''Checks whether a play is valid, based on the four conditions given. 
    Returns True if it is valid. False otherwise.'''
    # Check if the play satisfies all four conditions
    if (first_condition(play, player_id, turn_history, discard) and 
        second_condition(play, player_id, table, turn_history, 
                         phase_status, hand) and 
        third_condition(play, player_id, table, turn_history, 
                        phase_status, hand)
        and fourth_condition(play, player_id, table, turn_history, hand)):
        return True
    return False


def first_condition(play, player_id, turn_history, discard):
    ''' Checks whether the play satisfies the first condition. 
    Returns True if it does, False otherwise. Plays that are not pickup plays 
    are still considered to satisfy the first condition.'''
    # First, check if the play is a pick-up play. Then check whether it is
    # the first play of the turn. It is NOT the first play of the turn if the 
    # last turn tuple in turn_history is a play made by this player
    if play[0] == PLAY_ONE or play[0] == PLAY_TWO:
        if turn_history:
            last_player = turn_history[-1][0]
            if last_player == player_id:
                return False
    
    # If the play is a pickup play from the discard pile, check if the 
    # intended card to be picked up matches the card on the discard pile
    if play[0] == PLAY_TWO and play[1] != discard:
        return False
    
    return True


def second_condition(play, player_id, table, turn_history, phase_status, hand):
    '''Checks whether the play satisfies the second condition.
    Returns True if it does, False otherwise. Again, plays that are not phase 
    plays are still considered to satisfy the second condition'''
    # Check that the play is a phase play
    if play[0] == PLAY_THREE:
        declared_phase = play[1][0]
        required_phase = phase_status[player_id] + 1
        phase_play = play[1][1]
        
        # Check if the play occurs after a pickup play
        if not after_pickup(player_id, turn_history):
            return False

        # Next, check if the intended phase play is the phase type that the  
        # player is required to play for the current hand
        if declared_phase != required_phase:
            return False

        # Also check whether the player has already played a phase in the 
        # current hand. 
        table_phase = table[player_id][0]
        if table_phase:
            return False
        
        # Then, check that the player holds all cards in the attempted play.
        player_hand = hand.copy()
        for group in phase_play:
            for card in group:
                if card in player_hand:
                    player_hand.remove(card)
                else:
                    return False
        
        # Finally, check that the phase play matches the declared phase type
        if declared_phase not in phazed_phase_type(phase_play):
            return False
    return True


def third_condition(play, player_id, table, turn_history, phase_status, hand):
    '''Checks whether the play satisfies the third condition. 
    Returns True if it does, False otherwise. Note that plays that are not to
    the table will still be considered to satisfy the third condition.'''
    # Check that the play is a play to the table
    if play[0] == PLAY_FOUR:
        
        # Check that the play happens after a pickup play
        if not after_pickup(player_id, turn_history):
            return False
        
        # Check that the player has played their phase in the current hand
        table_phase = table[player_id][0]
        if not table_phase:
            return False
        
        # Check that the player holds the card in the attempted play
        if play[1][0] not in hand:
            return False
        
        # Check that the play is consistent with the group type the player is 
        # attempting to play to, with the following steps:
        declared_player = play[1][1][0]
        declared_group = play[1][1][1]
        declared_index = play[1][1][2]
        target = table[declared_player]
        # 1. check whether the index position is valid
        valid_index = False
        if len(target[1]) > declared_group:
            target_group = target[1][declared_group]
            if len(target_group) >= declared_index:
                valid_index = True
        if not valid_index:
            return False
        
        # 2. check that the card is consistent with the phase. 
        card = play[1][0]
        target_phase = target[0]
        target_group = target[1][declared_group]
        # Consider phase 1, phase 4, and group '1th' of phase 7:
        # (cards of the same value)
        if (target_phase == PHASE_ONE or target_phase == PHASE_FOUR or 
            target_phase == PHASE_SEVEN and declared_group == 1):
            target_group.append(card)
            if not same_value(target_group):
                return False
        # Consider phase 2: (same suit)
        if target_phase == PHASE_TWO:
            target_group.append(card)
            if not same_suit(target_group):
                return False
        # Consider phase 5: (run)
        if target_phase == PHASE_FIVE:
            target_group.insert(declared_index, card)
            if not run(target_group):
                return False
        # Consider phase 7, group 0: (run of same color)
        if target_phase == PHASE_SEVEN and declared_group == 0:
            target_group.insert(declared_index, card)
            if not run(target_group) or not same_color(target_group):
                return False
        # Consider phase 3(accumulation) and phase 6 (accum of same color)
        if target_phase == PHASE_THREE or target_phase == PHASE_SIX:
            card_sum = sum(CARD_VALUES[card_x[0]] for card_x in target_group)
            # Find the current accumulation, and locate its index
            for accum in ACCUMULATION_SEQUENCE:
                if card_sum >= accum:
                    curr_accum = accum
            accum_index = ACCUMULATION_SEQUENCE.index(curr_accum) 
            # if it's the end of the sequence, then the play is invalid
            if accum_index == len(ACCUMULATION_SEQUENCE) - 1: 
                return False
            # else, the end is not reached, continue testing
            next_accum = ACCUMULATION_SEQUENCE[accum_index + 1]
            new_card_sum = card_sum + CARD_VALUES[card[0]]
            # if the card is the last card, the accumulation must be complete
            if len(hand) == 1:
                if new_card_sum != next_accum:
                    return False
            # else, if the card is not the last card in hand, then the 
            # accumulation does not have to be complete
            if new_card_sum > next_accum:
                return False
            # For phase 6, the cards must be of the same color
            if target_phase == PHASE_SIX:
                target_group.append(card)
                if not same_color(target_group):
                    return False
    return True        
        

def fourth_condition(play, player_id, table, turn_history, hand):
    '''Checks if the fourth condition is satisfied. Returns True if yes, 
    False otherwise. Again, plays that are not discard plays are still 
    considered to satisfy the fourth condition.'''
    if play[0] == PLAY_FIVE:
        card = play[1]
        
        # Check that a pickup play happened before the discard play
        if not after_pickup(player_id, turn_history):
            return False
        
        # Check that the player holds the card
        if card not in hand:
            return False
        
        # Check that the player has not already discarded a card
        if turn_history[-1][-1][-1][0] == PLAY_FIVE:
            return False
        
        # Check that any accumulations are complete
        for player in table:
            if player[0] == PHASE_THREE or player[0] == PHASE_SIX:
                for group in player[1]:
                    card_sum = sum(CARD_VALUES[card_x[0]] for card_x in group)
                    if card_sum not in ACCUMULATION_SEQUENCE:
                        return False
    return True
    
    
def after_pickup(player_id, turn_history):
    '''Check if the play occurs after a pickup play. Returns True if it does,
    False otherwise. This function assumes that the play itself is not a pickup 
    play'''
    # Check that the turn_history is not empty
    if not turn_history:
        return False
    
    # Check that the last turn tuple in turn_history is of the same player
    if turn_history[-1][0] != player_id:
        return False
    return True