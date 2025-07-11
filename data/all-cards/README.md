
# Lorcana-JSON Format

This is the Lorcana-JSON format that is used to store the full database of card information. I pasted the Lorcana-JSON documentation below and will format it properly later.

# DOCS

What is this?

This project aims to collect data about all the cards in the Disney Lorcana trading card game, and to make that data accessible in an easy-to-use format.

It's aimed at developers of Disney Lorcana tools and websites, rather than players of the game. Having one source of data should save these developers time, since everybody doesn't individually have to collect and enter their own card data anymore.

This project is not affiliated with Ravensburger or Disney.
Data files explanation

There are four types of files: A metadata file; a file for each set and a zipfile with all individual set files; a file for each official deck and a zipfile with all individual deck files; and the file with all the cards.

Each data file type has its own use and fields:

    metadata.json contains data about the data files. Storing these values and occassionally retrieving just this file is an efficient way to check if the datafiles got updated, in which case you need to redownload them to get the latest version of the card data. This datablock is also included in the other data files under the "metadata" key. It consists of these fields:
        formatVersion: A string indicating the formatting version of the files, in major.minor.patch format. If this version string changes, the data structure was changed, and your tool that uses these data files might need adjustments. You can check the changelog for the exact changes
        generatedOn: An ISO 8601 formatted date and time string, indicating when the data files were generated. If this field changes, new cards may have been added or existing ones changed. You can check the changelog for the exact changes
        language: A two-letter code indicating which language this metadata is for: "de" for German, "en" for English, "fr" for French, and "it" for Italian
    setdata.[setCode].json contains data on all the cards in the set specified by the set code. There is a file like this for each released set. Each setdata file consists of these fields:
        code: The code of this set. This is already in the name of the set file, but it's here too for completion's sake
        hasAllCards: A boolean indicating whether all cards for this set have been released yet. true if all main cards (so excluding promos) of the set are in the datafile, false otherwise
        metadata: Contains the same metadata fields as in metadata.json, as described above
        name: The full name of this set
        number: The number of the set, within the set's 'type'. So both setcode "1" and "Q1" have 'number' 1, since the former is expansion 1 and the latter is quest 1. See also the type field
        prereleaseDate: The pre-release date for this set, when it was or will be available to buy from local game stores. Format is year-month-day. If the pre-release date isn't known yet, the value is 'null'
        releaseDate: The release date for this set, when it was or will be available to buy from large retailers. Format is year-month-day. If the release date isn't known yet, the value is 'null'
        type: What type of set this is. Most sets are type expansion, but sets like 'Illumineer's Quest: Deep Trouble' are type quest. The latter type may be missing some fields or values, and cards from these sets aren't allowed to be used during tournaments or official games
        cards: A list of card objects. The fields of each card object are described in the section below
    deckdata.[deckCode].json and deckdata.[deckCode].full.json contain data on all the cards in the deck specified by the deck code. The difference between the files is that the file with '.full' in the name contains full data on each card, whereas the other file only contains deck-specific card data. Each deck file consists of these fields:
        colors: A list of the card colors that this deck uses. Decks usually have two colors, but Ursula's deck in Illumineer's Quest: Deep Trouble doesn't have any, and the Gateway reward packs have four
        deckGroup: The code of the group this deck belongs to. For instance, with each new set they release two or three starter decks, and each of the starter decks for one set would have the same deckGroup value
        foilIds: A lot of decks include foil versions of one or more cards. For instance, starter decks contain foil versions of the cards on the packaging. This field contains a list of IDs of the cards that are foil in this deck
        metadata: Contains the same metadata fields as in metadata.json, as described above
        name: Some decks have a name. Starter decks for instance list the name on the back of the packaging. If a deck has a name, it's in this field. If it doesn't have a name, this field doesn't exist. Help wanted:: While the names of the English starter decks are easy to find, it's far harder for starter decks in other languages. If you know the names of the starter decks in non-English languages, please send a message, contact info is listed at the bottom of this page
        type: Different types of decks exist, for instance Starter Decks, Gateway Decks, and Quest decks. This field contains what type of deck this is
        cards: A list of card objects. For the contents of these objects, and the difference between the normal and the '.full' deckfiles, see the Deck Files paragraph in the next section
    allCards.json contains data on all the cards that have been released for Disney Lorcana. It consists of these fields:
        metadata: Contains the same metadata fields as in metadata.json, as described above
        sets: A dictionary with set data. There is a key for each set code, and the values are the same set data as described above for the set-specific datafiles (except the code field isn't here, since it's already the key of the dictionary, and there's no cards field here since there's already a general card list)
        cards: A list of card objects. The fields of each card object are described in the next section

Card data fields explanation

The allCards.json file and all the set files have a cards field, which contains a list of card objects.

This section describes the v2 format version. For the old deprecated v1 format version fields, click here

Each of those card objects consists of the following fields:

    abilities: A list of abilities of a Character, Location, or Item card. For cards without abilities, this field doesn't exist. Each ability entry is a dictionary containing (some of) the following fields:
        fullText contains the entire ability text as printed on the card, including newline characters
        type indicates what type of ability this is, one of 'activated' (pay cost to activate effect), 'keyword' (prenamed abilities), 'static' (always active), or 'triggered' (activated on certain events)
        'keyword'-type abilities are prenamed abilities, and ability entries with this type have the following extra fields:
            keyword contains the name of the ability's keyword ('Ward', 'Resist', etc.)
            keywordValue contains the 'value' part of a keyword, so for 'Resist +1', this field would contain the '+1' part. For abilities like 'Shift: Discard an Action card', this field contains the part after the colon
            keywordValueNumber contains the numeric part of the keywordValue, if it is numeric. So for 'Resist +1', this would be 1
            reminderText contains just the reminder text of a keyword ability, so the part between brackets. Most but not all cards with keyword abilities have reminder text for those keywords
        Other types of abilities are named abilities, and they have the following extra fields:
            effect is the text of what the ability actually does
            name is the name of the ability, shown at the start of the ability in a distinct label
            'activated'-type abilities are abilities that require you to actively pay a cost (exerting, paying ink, etc.) before the effect fires. Ability entries with this type have the following extra fields:
                costs is a list of each separate cost that needs to be paid to be able to activate this ability
                costsText is the costs as a single string
    artists: A list of the name(s) of the artist(s) that drew the art for this card. This will usually contain just one entry, but some cards have multiple artists. See also the artistsText field
    artistsText: The artist(s) that drew the card as it's printed on the bottom left of the card. See also the artists field
    bannedSince: Very rarely, Ravensburger bans certain cards from Constructed tournaments. If this card has been banned, this field exists and is set to the date when the ban went or will go into effect. Note that this means they're banned specifically in official Constructed tournaments, and the card can still be used in Sealed and Draft events. For cards that haven't been banned, this field doesn't exist
    clarifications: Some cards have extra clarifications for how they work or interact with other cards. This field is a list of those clarifications. For cards without clarifications, this field doesn't exist. The text can contain newline characters
    code: This field is the two-character code for this card that the official app uses internally when saving a deck. It is the base-62 version of the card ID (digits higher than 9 use lowercase a-z and then uppercase A-Z). See also the id field
    color: The name of the color of the card. One of Amber, Amethyst, Emerald, Ruby, Sapphire, Steel. Cards from Quest-type sets don't have a color, so for those, this field is an empty string. For dual-ink cards, it lists both colors separated by a '-'; see also the colors field
    colors: Only dual-ink cards have this field. This is a list field with each color of the card as a separate string. For single-color cards or cards with no color, this field doesn't exist. See also the color field
    cost: How much Ink this card costs to play
    effects: A list of strings with an entry for each effect an Action card has. For cards without effects, this field doesn't exist
    enchantedId: For cards that have an Enchanted version, this field contains the ID of that Enchanted card. For other cards, this field doesn't exist. See also the nonEnchantedId field
    errata: Some cards have errata, correcting mistakes on the card, and/or improving phrasing. This field is a list of those corrections. For cards without errata, this field doesn't exist. The text can contain newline characters
    externalLinks: This dictionary contains information to link this dataset to other Lorcana-related datasets. The dictionary itself always exists, but each field inside it only exists when it is known for the card. Available external link fields are:
        cardTraderId: The ID used by the CardTrader card marketplace for this card. You can use their API and this ID to look up pricing data of this card
        cardTraderUrl: The page of this card on the CardTrader card marketplace. This is not a referral link, so LorcanaJSON doesn't earn any money when this link is used
        cardmarketId: The ID used by the Cardmarket card marketplace for this card. On their website, you can download a price guide, and use this ID to look up pricing data of this card
        cardmarketUrl: The page of this card on the Cardmarket card marketplace. This is not a referral link, so LorcanaJSON doesn't earn any money when this link is used
        tcgPlayerId: The ID used by the TCGplayer card marketplace. You can use the data from TCGCSV and this ID to look up pricing data of this card
        tcgPlayerUrl: The page of this card on the TCGplayer card marketplace. This is not a referral link, so LorcanaJSON doesn't earn any money when this link is used
    flavorText: The flavor text at the bottom of a card. This has no gameplay effect, but does improve the feel of the card. For cards without flavor text, this field doesn't exist. The text can contain newline characters
    foilTypes: A list of all the foil types the card can have. 'None' means no foiling. Since this is impossible to fully manually verify, this data may not be 100% accurate, especially for 'Special'-rarity cards. For cards where isExternalReveal exists and is set to true, and for some other special cards, this field does not exist
    fullIdentifier: The full identifier as displayed on the bottom-left of each card, for instance 9/204 • EN • 3. The formatting may be different for promo cards. See also the number and setNumber fields
    fullName: The full name of the card. For characters and locations, this is the name plus the version, separated by a dash. For other card types this is the same as the name field. See also the name, version and simpleName fields
    fullText: The entire main gameplay text on the card as printed, not split up into abilities or effects. Does not include the flavor text. This field always exists, but can be an empty string on cards without rules text. The text can contain newline characters. See also the fullTextSections field
    fullTextSections: A list of all the sections of the main gameplay text, with each ability or effect as a separate entry. Does not include the flavor text. This field always exists, but can be an empty list on cards without rules text. Each entry can contain newline characters. See also the fullText field
    historicData: This field only exists on cards that have had errata or changes to text on the card. The most well-known example is "Bucky - Squirrel Squeak Tutor" (ID 289), which got changed a lot. But other smaller changes have been made too. If it exists, it is a list of dictionaries, with each entry containing the card fields that have been changed in the errata, plus a field called usedUntil that contains the date in yyyy-mm-dd format until when this historic data was used
    id: A unique number identifying the card. For the first set, this id is identical to the number field; for subsequent sets, the id keeps counting up (so the first card of set 2 has an id one higher than the last card of set 1). The id is identical between different language versions of the same card
    images: A dictionary with several URLs of card images. These images are the same ones as used in the official Disney Lorcana app.
    The fields in this dictionary are:
        full: The URL of the card image at full size, usually 1468 by 2048 pixels
        fullFoil: Some foil versions of cards have slightly different art than the non-foil version (for instance Louie, Dewey, and Huey from set 8 [IDs 1665, 1666, and 1667]). For these cards, this field exists and the URL points to the full art of the foil card. For cards that don't have different art for their foil version, this field doesn't exist
        thumbnail: The URL of the card image at thumbnail size, usually 367 by 512 pixels
        foilMask: A mask of the full card image that the official Disney Lorcana app uses to draw the foil effect, usually 1468 by 2048 pixels. Not all cards have this field
        varnishMask: A mask of the full card image that the official Disney Lorcana app uses to draw the varnish effect, usually 1468 by 2048 pixels. Not all cards have this field. See also the varnishType field
    Note: If the isExternalReveal field exists and is set to true, this card isn't in the official app yet, so only the 'full' image field will be set
    inkwell: true if this card is allowed to be put into the inkwell as ink, so if it has the extra decoration around the cost in the top left of the card, and false otherwise
    isExternalReveal: If this field exists and is true, the data from this card didn't come from the official app, but the card image came from another official Ravensburger source. Practically, this means that the images field will probably only have the full URL set, and it will be in another format than usual. This field doesn't exist if the data for this card came from the official app
    keywordAbilities: A list of the keyword abilities of this character card, without the reminder text. For keyword abilities with a value, like Shift X or Challenger +X, the list entry doesn't include that value. For cards without keyword abilities, this field doesn't exist
    lore: For character cards, this is the amount of lore this character earns for a player when they quest with it. For characters that can't quest, this value is 0. For location cards, this is the amount of lore this location card earns at the start of each turn. For other card types, this field doesn't exist
    maxCopiesInDeck: When building a deck, you can usually add a maximum of 4 copies of a card to that deck. Some cards are exceptions to that rule. For those cards, this field exists and is set to the maximum amount that applies for this card. See for example the card Dalmatian Puppy - Tail Wagger (IDs 436-440): the card allows 99 copies of it in a deck, so the value of this field is set to '99'. If the card allows an unlimited amount of copies, like Microbots (ID 1366), this field is set to 'null'. If no special limit applies, this field doesn't exist
    moveCost: For location cards, this is the amount of ink it costs to move a character to this location. For other cards, this field doesn't exist
    name: The main name of the card. For characters and locations, this is the character or location name without the small version subtitle (So the "Minnie Mouse" part of "Minnie Mouse - Stylish Surfer"). For other card types, this is the same as the fullName field. See also the fullName and version fields
    nonEnchantedId: For Enchanted-rarity cards, this field contains the ID of the non-Enchanted version of the same card. For non-Enchanted-rarity cards, this field doesn't exist. See also the enchantedId field
    nonPromoId: Special versions of some cards are released at events or at other occasions, as promo versions. For these cards, this field points to the ID of the non-promo version of the same card. For other cards, this field doesn't exist. See also the promoIds field
    number: The number of the card inside its set, shown as number/totalCards in the bottom left of the card and in the fullIdentifier field. For 'Special'-rarity cards, this number is the promo number instead, so a set might have two cards with number 1, one Special and one non-Special. This doesn't necessarily mean the cards are related, for that see the promoIds and nonSpecialId fields. For a unique card identifier, see the id field
    promoGrouping: This field contains which grouping a promo card belongs to. A grouping is different from a setcode. For instance, the promo card Minnie Mouse - Wide-Eyed Diver (ID 674) has the full identifier '16/P1 • EN • 2'. The grouping here is 'P1'. Cards from different sets can belong to the same grouping. Available groupings are 'P1', 'P2', 'C1', 'C2', 'D23'; more will probably be added at a later time. This field doesn't exist for non-promo cards
    promoIds: Special versions of some cards are released at events or at other occasions, as promo versions. For cards that have such promo versions, this field has a list of IDs of those promo versions of this non-promo card. For cards without a promo version, this field doesn't exist. See also the nonPromoId field
    rarity: The rarity of this card. One of Common, Uncommon, Rare, Super Rare, Legendary, Enchanted, or Special (the latter is used for promos or other special releases)
    setCode: A string representation of the set code, which is the set number for 'normal' cards, and Q1 for Illumineer's Quest cards. This is exactly how it's printed as the last part of the identifier at the bottom-left of each card.
    This set code is also a key in the "sets" dictionary inside the "allCards.json" file, linking to the set name and other set data.
    This field does not exist in the set-specific data files, since it doesn't make sense there. See also the setNumber field
    simpleName: The full name like in the fullName field, but simplified: without the dash between name and version subtitle (for character and location cards), without special characters like '!' and '.', and entirely in lower-case. Special versions of letters are simplified too (for instance: "Te Kā - The Burning One" has the simpleName "te ka the burning one"). Quotemarks in possessives ("captain colonel's lieutenant") and dashes between words ("minnie mouse wide-eyed diver") are kept, since that's related to basic spelling. This field should make it easier to implement this data in a search engine, since most people won't use the dash or other special characters when searching for a card, so you can match their query against this field. See also the fullName field
    story: The name of the story (movie, TV show, etc.) that the card is from or that it references
    strength: The strength of a character card, so how much damage it does to another character during a challenge. For card types other than characters, this field doesn't exist
    subtypes: A list of the subtypes of this card. For characters, this can have entries like Dreamborn and Princess. For song actions, this contains 'Song'. The order of the list is the same as on the card. For cards without subtypes, this field doesn't exist. See also the subtypesText field
    subtypesText: If this card has one or more subtypes, this field contains those subtypes as one string, just like it's printed on the card. For cards without subtypes, this field doesn't exist. See also the subtypes field
    type: What kind of card this is. One of Action, Character, Item, Location
    variant: Some cards have multiple variants that only have different art (for instance Dalmatian Puppy has ID 436 to 440). These are differentiated by a letter after the card number (for Dalmatian Puppy, letters 'a' to 'e'). This field contains that letter. For cards without variants, this field doesn't exist. See also the variantIds field
    variantIds: Some cards have multiple variants that only have different art (for instance Dalmatian Puppy has ID 436 to 440). This field contains a list of the IDs of the other cards belonging to this variant. For cards without variants, this field doesn't exist. See also the variant field
    varnishType: A few cards have a special varnish effect. If this card is varnished, this field exists and is set to the exact varnish type. For cards that don't have a varnish effect, this field doesn't exist. See also the varnishMask subfield of the images dictionary
    version: The version subtitle of a character or location card, written below the name (So the "Stylish Surfer" part of "Minnie Mouse - Stylish Surfer"). For other card types, this field doesn't exist. See also the fullName and name fields
    willpower: The willpower of a character or location card, so how much damage it can take before it is banished. For other card types, this field doesn't exist

Deck files
The deck files also have a cards field with card objects. The difference between the deckdata.[deckCode].json and the deckdata.[deckCode].full.json deckfiles is that the card objects in the former only contain the following fields, while the card objects in the latter, '.full', deck files contain these fields in addition to all the fields listed above. The fields specific to card objects in the deck files are:

    amount: How many copies of this card are in the deck
    id: The ID of the card, uniquely identifying it. See the explanation for the id field in the Card data fields explanation section for a more extensive explanation
    isFoil: Whether the card is foil in this deck. If 'true', the id of this card is then also in the foilIds field of the deck

Disney Lorcana symbols

Certain text fields (abilities, clarifications, effects, errata, fullText, fullTextSections, historicData) can have special Unicode characters in them that resemble the game-specific icons as closely as possible:

    ⟳ (Unicode character U+27F3): Exert
    ⬡ (Unicode character U+2B21): Ink (usually in activation costs)
    ◊ (Unicode character U+25CA): Lore (usually used to indicate the lore gain when questing)
    ¤ (Unicode character U+00A4): Strength
    ⛉ (Unicode character U+26C9): Willpower
    ◉ (Unicode character U+25C9): Inkwell (the decoration around the card cost), meant to symbolise whether the card is allowed to be put into your inkwell. The character isn't too similar to the actual card symbol, but it's the closest available
    • (Unicode character U+2022): Bullet point that separates different subtypes, and is also used in lists on cards (for instance Maui's Fish Hook, ID 568)

