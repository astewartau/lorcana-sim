"""Tests for keyword ability implementations."""

import pytest
from lorcana_sim.abilities.keywords import (
    KeywordRegistry, SingerAbility, EvasiveAbility, BodyguardAbility,
    ShiftAbility, SupportAbility, WardAbility, RushAbility, ResistAbility
)
from lorcana_sim.models.abilities.base_ability import AbilityType
from lorcana_sim.models.cards.character_card import CharacterCard
from lorcana_sim.models.cards.action_card import ActionCard
from lorcana_sim.models.cards.base_card import CardColor, Rarity


def create_test_character(name: str, abilities: list = None) -> CharacterCard:
    """Helper to create test character cards."""
    return CharacterCard(
        id=1,
        name=name,
        version="Test Version",
        full_name=name,
        cost=3,
        color=CardColor.AMBER,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=1,
        story="Test",
        strength=2,
        willpower=3,
        lore=1,
        abilities=abilities or []
    )


def create_test_song(cost: int, singer_cost: int) -> ActionCard:
    """Helper to create test song cards."""
    from lorcana_sim.models.abilities.base_ability import Ability, AbilityType
    
    # Create an ability with the proper song text format
    song_ability = Ability(
        name="Song Effect",
        type=AbilityType.STATIC,
        effect=f"A character with cost {singer_cost} or more can sing this song for free.",
        full_text=f"A character with cost {singer_cost} or more can sing this song for free."
    )
    
    song = ActionCard(
        id=1,
        name="Test Song",
        version="Test Version",
        full_name="Test Song",
        cost=cost,
        color=CardColor.AMBER,
        inkwell=True,
        rarity=Rarity.COMMON,
        set_code="TEST",
        number=1,
        story="Test",
        abilities=[song_ability]
    )
    return song


class TestKeywordRegistry:
    """Test the keyword registry system."""
    
    def test_registry_has_implementations(self):
        """Test that the registry has the expected keyword implementations."""
        registered = KeywordRegistry.get_registered_keywords()
        
        assert 'Singer' in registered
        assert 'Evasive' in registered
        assert 'Bodyguard' in registered
        assert 'Shift' in registered
        assert 'Support' in registered
        assert 'Ward' in registered
        assert 'Rush' in registered
        assert 'Resist' in registered
    
    def test_get_implementation(self):
        """Test getting keyword implementations."""
        singer_impl = KeywordRegistry.get_implementation('Singer')
        evasive_impl = KeywordRegistry.get_implementation('Evasive')
        unknown_impl = KeywordRegistry.get_implementation('UnknownKeyword')
        
        assert singer_impl == SingerAbility
        assert evasive_impl == EvasiveAbility
        assert unknown_impl.__name__ == 'UnknownKeywordAbility'
    
    def test_create_keyword_ability(self):
        """Test factory method for creating keyword abilities."""
        singer = KeywordRegistry.create_keyword_ability('Singer', value=5)
        
        assert isinstance(singer, SingerAbility)
        assert singer.keyword == 'Singer'
        assert singer.value == 5
        assert singer.type == AbilityType.KEYWORD


class TestSingerAbility:
    """Test Singer keyword ability implementation."""
    
    def test_singer_creation(self):
        """Test creating Singer ability."""
        singer = SingerAbility(
            name="Singer",
            type=AbilityType.KEYWORD,
            effect="Singer ability",
            full_text="Singer 5",
            keyword="Singer",
            value=5
        )
        
        assert singer.keyword == "Singer"
        assert singer.value == 5
        assert singer.get_effective_sing_cost() == 5
        assert str(singer) == "Singer 5"
    
    def test_singer_without_value(self):
        """Test Singer ability without value."""
        singer = SingerAbility(
            name="Singer",
            type=AbilityType.KEYWORD,
            effect="Singer ability",
            full_text="Singer",
            keyword="Singer",
            value=None
        )
        
        assert singer.get_effective_sing_cost() == 0
        assert str(singer) == "Singer"
    
    def test_can_sing_song(self):
        """Test if Singer can sing specific songs."""
        singer_5 = SingerAbility(
            name="Singer",
            type=AbilityType.KEYWORD,
            effect="Singer ability",
            full_text="Singer 5",
            keyword="Singer",
            value=5
        )
        
        song_cost_3 = create_test_song(cost=4, singer_cost=3)
        song_cost_5 = create_test_song(cost=6, singer_cost=5)
        song_cost_7 = create_test_song(cost=8, singer_cost=7)
        
        # Singer 5 can sing songs requiring cost 5 or less
        assert singer_5.can_sing_song(song_cost_3) == True
        assert singer_5.can_sing_song(song_cost_5) == True
        assert singer_5.can_sing_song(song_cost_7) == False
    
    def test_get_cost_reduction(self):
        """Test cost reduction calculation."""
        singer_5 = SingerAbility(
            name="Singer",
            type=AbilityType.KEYWORD,
            effect="Singer ability",
            full_text="Singer 5",
            keyword="Singer",
            value=5
        )
        
        song = create_test_song(cost=6, singer_cost=5)
        
        # When singer can sing the song, reduction equals the song's full cost
        reduction = singer_5.get_cost_reduction(song)
        assert reduction == 6  # Full cost of the song
    
    def test_passive_ability(self):
        """Test that Singer is a passive ability."""
        singer = SingerAbility(
            name="Singer",
            type=AbilityType.KEYWORD,
            effect="Singer ability",
            full_text="Singer 5",
            keyword="Singer",
            value=5
        )
        
        # Singer should not be activatable
        assert singer.can_activate(None) == False


class TestEvasiveAbility:
    """Test Evasive keyword ability implementation."""
    
    def test_evasive_creation(self):
        """Test creating Evasive ability."""
        evasive = EvasiveAbility(
            name="Evasive",
            type=AbilityType.KEYWORD,
            effect="Evasive ability",
            full_text="Evasive",
            keyword="Evasive",
            value=None
        )
        
        assert evasive.keyword == "Evasive"
        assert evasive.modifies_challenge_rules() == True
        assert str(evasive) == "Evasive"
    
    def test_can_be_challenged_by(self):
        """Test Evasive challenge restrictions."""
        evasive_ability = EvasiveAbility(
            name="Evasive",
            type=AbilityType.KEYWORD,
            effect="Evasive ability",
            full_text="Evasive",
            keyword="Evasive",
            value=None
        )
        
        # Create characters
        evasive_challenger = create_test_character("Evasive Challenger", [evasive_ability])
        normal_challenger = create_test_character("Normal Challenger", [])
        
        # Evasive character can challenge another evasive character
        assert evasive_ability.can_be_challenged_by(evasive_challenger) == True
        
        # Normal character cannot challenge evasive character
        assert evasive_ability.can_be_challenged_by(normal_challenger) == False
    
    def test_passive_ability(self):
        """Test that Evasive is a passive ability."""
        evasive = EvasiveAbility(
            name="Evasive",
            type=AbilityType.KEYWORD,
            effect="Evasive ability",
            full_text="Evasive",
            keyword="Evasive",
            value=None
        )
        
        # Evasive should not be activatable
        assert evasive.can_activate(None) == False


class TestBodyguardAbility:
    """Test Bodyguard keyword ability implementation."""
    
    def test_bodyguard_creation(self):
        """Test creating Bodyguard ability."""
        bodyguard = BodyguardAbility(
            name="Bodyguard",
            type=AbilityType.KEYWORD,
            effect="Bodyguard ability",
            full_text="Bodyguard",
            keyword="Bodyguard",
            value=None
        )
        
        assert bodyguard.keyword == "Bodyguard"
        assert bodyguard.can_enter_play_exerted() == True
        assert bodyguard.modifies_challenge_targeting() == True
        assert str(bodyguard) == "Bodyguard"
    
    def test_bodyguard_challenge_rules(self):
        """Test Bodyguard challenge targeting rules."""
        bodyguard_ability = BodyguardAbility(
            name="Bodyguard",
            type=AbilityType.KEYWORD,
            effect="Bodyguard ability",
            full_text="Bodyguard",
            keyword="Bodyguard",
            value=None
        )
        
        # Create characters
        bodyguard_char = create_test_character("Bodyguard Character", [bodyguard_ability])
        normal_char = create_test_character("Normal Character", [])
        
        # Test that bodyguard character can be identified
        assert bodyguard_ability._has_bodyguard(bodyguard_char) == True
        assert bodyguard_ability._has_bodyguard(normal_char) == False
    
    def test_passive_ability(self):
        """Test that Bodyguard is a passive ability."""
        bodyguard = BodyguardAbility(
            name="Bodyguard",
            type=AbilityType.KEYWORD,
            effect="Bodyguard ability",
            full_text="Bodyguard",
            keyword="Bodyguard",
            value=None
        )
        
        # Bodyguard should not be activatable
        assert bodyguard.can_activate(None) == False


class TestShiftAbility:
    """Test Shift keyword ability implementation."""
    
    def test_shift_creation(self):
        """Test creating Shift ability."""
        shift = ShiftAbility(
            name="Shift",
            type=AbilityType.KEYWORD,
            effect="Shift ability",
            full_text="Shift 6",
            keyword="Shift",
            value=6
        )
        
        assert shift.keyword == "Shift"
        assert shift.value == 6
        assert shift.get_shift_cost() == 6
        assert shift.provides_alternative_play_cost() == True
        assert str(shift) == "Shift 6"
    
    def test_shift_alternative_cost(self):
        """Test Shift alternative cost mechanics."""
        shift = ShiftAbility(
            name="Shift",
            type=AbilityType.KEYWORD,
            effect="Shift ability",
            full_text="Shift 4",
            keyword="Shift",
            value=4
        )
        
        assert shift.get_alternative_cost() == 4
        assert shift.requires_target_for_play() == True
    
    def test_passive_ability(self):
        """Test that Shift is a passive ability."""
        shift = ShiftAbility(
            name="Shift",
            type=AbilityType.KEYWORD,
            effect="Shift ability",
            full_text="Shift 6",
            keyword="Shift",
            value=6
        )
        
        assert shift.can_activate(None) == False


class TestSupportAbility:
    """Test Support keyword ability implementation."""
    
    def test_support_creation(self):
        """Test creating Support ability."""
        support = SupportAbility(
            name="Support",
            type=AbilityType.KEYWORD,
            effect="Support ability",
            full_text="Support",
            keyword="Support",
            value=None
        )
        
        assert support.keyword == "Support"
        assert support.triggers_on_quest() == True
        assert support.modifies_quest_effects() == True
        assert support.is_optional() == True
        assert str(support) == "Support"
    
    def test_support_targeting(self):
        """Test Support targeting rules."""
        support = SupportAbility(
            name="Support",
            type=AbilityType.KEYWORD,
            effect="Support ability",
            full_text="Support",
            keyword="Support",
            value=None
        )
        
        supporting_char = create_test_character("Supporting Character")
        target_char = create_test_character("Target Character")
        
        # Can support other characters but not self
        assert support.can_support_character(target_char, supporting_char) == True
        assert support.can_support_character(supporting_char, supporting_char) == False
    
    def test_passive_ability(self):
        """Test that Support is a triggered ability."""
        support = SupportAbility(
            name="Support",
            type=AbilityType.KEYWORD,
            effect="Support ability",
            full_text="Support",
            keyword="Support",
            value=None
        )
        
        assert support.can_activate(None) == False


class TestWardAbility:
    """Test Ward keyword ability implementation."""
    
    def test_ward_creation(self):
        """Test creating Ward ability."""
        ward = WardAbility(
            name="Ward",
            type=AbilityType.KEYWORD,
            effect="Ward ability",
            full_text="Ward",
            keyword="Ward",
            value=None
        )
        
        assert ward.keyword == "Ward"
        assert ward.protects_from_targeting() == True
        assert ward.allows_challenges() == True
        assert ward.allows_owner_targeting() == True
        assert ward.modifies_targeting_rules() == True
        assert str(ward) == "Ward"
    
    def test_passive_ability(self):
        """Test that Ward is a passive ability."""
        ward = WardAbility(
            name="Ward",
            type=AbilityType.KEYWORD,
            effect="Ward ability",
            full_text="Ward",
            keyword="Ward",
            value=None
        )
        
        assert ward.can_activate(None) == False


class TestRushAbility:
    """Test Rush keyword ability implementation."""
    
    def test_rush_creation(self):
        """Test creating Rush ability."""
        rush = RushAbility(
            name="Rush",
            type=AbilityType.KEYWORD,
            effect="Rush ability",
            full_text="Rush",
            keyword="Rush",
            value=None
        )
        
        assert rush.keyword == "Rush"
        assert rush.can_challenge_immediately() == True
        assert rush.ignores_summoning_sickness_for_challenges() == True
        assert rush.allows_quest_immediately() == False
        assert rush.modifies_challenge_timing() == True
        assert rush.is_passive_modifier() == True
        assert str(rush) == "Rush"
    
    def test_passive_ability(self):
        """Test that Rush is a passive ability."""
        rush = RushAbility(
            name="Rush",
            type=AbilityType.KEYWORD,
            effect="Rush ability",
            full_text="Rush",
            keyword="Rush",
            value=None
        )
        
        assert rush.can_activate(None) == False


class TestResistAbility:
    """Test Resist keyword ability implementation."""
    
    def test_resist_creation(self):
        """Test creating Resist ability."""
        resist = ResistAbility(
            name="Resist",
            type=AbilityType.KEYWORD,
            effect="Resist ability",
            full_text="Resist +2",
            keyword="Resist",
            value=2
        )
        
        assert resist.keyword == "Resist"
        assert resist.value == 2
        assert resist.get_damage_reduction() == 2
        assert resist.modifies_damage_calculation() == True
        assert resist.is_passive_damage_modifier() == True
        assert resist.applies_to_all_damage_sources() == True
        assert str(resist) == "Resist +2"
    
    def test_damage_reduction(self):
        """Test damage reduction calculations."""
        resist_2 = ResistAbility(
            name="Resist",
            type=AbilityType.KEYWORD,
            effect="Resist ability",
            full_text="Resist +2",
            keyword="Resist",
            value=2
        )
        
        # Test various damage amounts
        assert resist_2.reduce_incoming_damage(5) == 3  # 5 - 2 = 3
        assert resist_2.reduce_incoming_damage(2) == 0  # 2 - 2 = 0 (minimum 0)
        assert resist_2.reduce_incoming_damage(1) == 0  # 1 - 2 = 0 (minimum 0)
        assert resist_2.reduce_incoming_damage(0) == 0  # 0 - 2 = 0 (minimum 0)
    
    def test_passive_ability(self):
        """Test that Resist is a passive ability."""
        resist = ResistAbility(
            name="Resist",
            type=AbilityType.KEYWORD,
            effect="Resist ability",
            full_text="Resist +1",
            keyword="Resist",
            value=1
        )
        
        assert resist.can_activate(None) == False