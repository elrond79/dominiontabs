from __future__ import print_function
import subprocess
import shutil
import os
import contextlib

import pytest

from domdiv import main
from domdiv import cards as domdiv_cards


@pytest.fixture
def rmtestcardb(request):
    def rmd():
        testcardb_dir = os.path.join(str(request.config.rootdir), "tools/card_db")
        if os.path.exists(testcardb_dir):
            print("removing {}".format(testcardb_dir))
            shutil.rmtree(testcardb_dir)

    request.addfinalizer(rmd)


def test_cardread():
    cardsExpected = 574

    options = main.parse_opts([])
    options.data_path = "."
    cards = main.read_card_data(options)
    assert len(cards) == cardsExpected
    valid_cardsets = {
        u"base",
        u"dominion1stEdition",
        u"dominion2ndEdition",
        u"dominion2ndEditionUpgrade",
        u"intrigue1stEdition",
        u"intrigue2ndEdition",
        u"intrigue2ndEditionUpgrade",
        u"seaside",
        u"alchemy",
        u"prosperity",
        u"cornucopia extras",
        u"cornucopia",
        u"hinterlands",
        u"dark ages",
        u"dark ages extras",
        u"guilds",
        u"adventures",
        u"adventures extras",
        u"empires",
        u"empires extras",
        u"nocturne",
        u"nocturne extras",
        u"promo",
        u"renaissance",
        u"extras",
        u"animals",
    }
    for c in cards:
        assert isinstance(c, domdiv_cards.Card)
        assert c.cardset_tag in valid_cardsets

    # Option modified card count
    options = main.parse_opts(
        ["--no-trash", "--curse10", "--start-decks", "--include-blanks", "7"]
    )
    options = main.clean_opts(options)
    options.data_path = "."
    cards = main.read_card_data(options)
    # Total delta cards is +28 from
    #      Trash:       -1 * 3 sets = -3
    #      Curse:       +2 * 4 sets = +8
    #      Start Decks: +4 * 4 sets = +16
    #      Blanks:      +7          = +7
    assert len(cards) == cardsExpected + 28


def test_languages():
    languages = main.get_languages("card_db")
    for lang in languages:
        print("checking " + lang)
        # for now, just test that they load
        options = main.parse_opts(["--language", lang])
        options.data_path = "."
        cards = main.read_card_data(options)
        assert cards, '"{}" cards did not read properly'.format(lang)
        cards = main.add_card_text(cards, "en_us")
        cards = main.add_card_text(cards, lang)
        if lang == "it":
            assert "Maledizione" in [card.name for card in cards]
        elif lang == "de":
            assert "Fluch" in [card.name for card in cards]


@contextlib.contextmanager
def change_cwd(d):
    curdir = os.getcwd()
    try:
        os.chdir(d)
        yield
    finally:
        os.chdir(curdir)


def test_languagetool_run(pytestconfig):
    with change_cwd(str(pytestconfig.rootdir)):
        cmd = "python tools/update_language.py"
        print(cmd)
        assert subprocess.check_call(cmd.split()) == 0
        cmd = "diff -rwB src/domdiv/card_db tools/card_db"
        try:
            out = subprocess.check_output(cmd.split(), stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            assert e.output == ""
        assert out.decode("utf-8") == ""


def test_only_type():
    options = main.parse_opts(
        [
            "--expansions",
            "base",
            "alchemy",
            "--include-blanks",
            "5",
            "--only-type-any",
            "blank",
            "curse",
            "--only-type-all",
            "attack",
            "action",
        ]
    )
    options = main.clean_opts(options)
    options.data_path = "."
    cards = main.read_card_data(options)
    cards = main.filter_sort_cards(cards, options)
    # Total 8 from
    #      Blank:         +5 added in options
    #      Curse:         +1 from base
    #      Action Attack: +2 from Alchemy
    assert len(cards) == 8


def test_expansion():
    # test that we can use --expansion or
    # --expansions, that we can have multiple
    # items with a single flag, that * syntax
    # works, that we can use either the
    # cardset tag or name, and that capitalziation
    # doesn't matter
    options = main.parse_opts(
        [
            "--expansion",
            "advEntUres",
            "dominion 2nd*",
            "--expansions=intrigue1stEdition",
        ]
    )
    options = main.clean_opts(options)
    options.data_path = "."
    cards = main.read_card_data(options)
    cards = main.filter_sort_cards(cards, options)
    card_sets = set(x.cardset.lower() for x in cards)
    assert card_sets == {
        "adventures",
        "dominion 2nd edition",
        "dominion 2nd edition upgrade",
        "intrigue 1st edition",
    }


def test_exclude_expansion():
    # test that we can use --exclude-expansion or
    # --exclude-expansions, that we can have multiple
    # items with a single flag, that * syntax
    # works, that we can use either the
    # cardset tag or name, and that capitalziation
    # doesn't matter
    options = main.parse_opts(
        [
            "--expansions",
            "adventures",
            "dominion*",
            "intrigue*",
            "--exclude-expansions",
            "dominiOn1stEditIon",
            "intrigue 2nd*",
            "--exclude-expansion",
            "dominion 2nd edition",
        ]
    )
    options = main.clean_opts(options)
    options.data_path = "."
    cards = main.read_card_data(options)
    cards = main.filter_sort_cards(cards, options)
    card_sets = set(x.cardset.lower() for x in cards)
    assert card_sets == {
        "adventures",
        "dominion 2nd edition upgrade",
        "intrigue 1st edition",
    }
