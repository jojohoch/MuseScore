/*
 * SPDX-License-Identifier: GPL-3.0-only
 * MuseScore-Studio-CLA-applies
 *
 * MuseScore Studio
 * Music Composition & Notation
 *
 * Copyright (C) 2026 MuseScore Limited and others
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 3 as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

#include <gtest/gtest.h>

#include "io/file.h"

#include "engraving/dom/chord.h"
#include "engraving/dom/masterscore.h"
#include "engraving/dom/measure.h"
#include "engraving/dom/note.h"
#include "engraving/dom/segment.h"
#include "engraving/editing/undo.h"
#include "engraving/types/constants.h"

#include "utils/scorerw.h"
#include "utils/scorecomp.h"

using namespace mu::engraving;

// Four staves with chords on the second and third staff
static const String BASE_SCORE(u"splitstaff_data/splitstaff03-ref.mscx");

class Engraving_EightVoicesTests : public ::testing::Test
{
};

static Chord* firstChord(Score* score, staff_idx_t staffIdx)
{
    const track_idx_t track = staff2track(staffIdx);
    for (Segment* s = score->firstSegment(SegmentType::ChordRest); s; s = s->next1(SegmentType::ChordRest)) {
        EngravingItem* e = s->element(track);
        if (e && e->isChord()) {
            return toChord(e);
        }
    }
    return nullptr;
}

static String fileText(const String& path)
{
    muse::ByteArray data;
    muse::io::File::readFile(path, data);
    return String::fromUtf8(data);
}

static String versionTag(const char* version)
{
    return String(u"<museScore version=\"%1\">").arg(String::fromAscii(version));
}

TEST_F(Engraving_EightVoicesTests, voicesBeyondFourAreMarkedAndRoundTrip)
{
    MasterScore* score = ScoreRW::readScore(BASE_SCORE);
    ASSERT_TRUE(score);
    EXPECT_TRUE(ScoreRW::saveScore(score, u"eightvoices-original.mscx"));

    // Move the first chord of the second staff to voice 6
    Chord* chord = firstChord(score, 1);
    ASSERT_TRUE(chord);
    const Fraction tick = chord->tick();
    const int pitch = chord->upNote()->pitch();

    score->select(chord->upNote());
    score->startCmd(TranslatableString::untranslatable("Eight voices tests"));
    score->changeSelectedElementsVoice(5);
    score->endCmd();

    const track_idx_t movedTrack = staff2track(1, 5);
    EngravingItem* moved = score->tick2segment(tick, true, SegmentType::ChordRest)->element(movedTrack);
    ASSERT_TRUE(moved && moved->isChord());

    // Saved with the eight voices marker
    EXPECT_TRUE(ScoreRW::saveScore(score, u"eightvoices-moved.mscx"));
    const String saved = fileText(u"eightvoices-moved.mscx");
    EXPECT_TRUE(saved.contains(versionTag(Constants::MSC_VERSION_EIGHT_VOICES_STR)));

    // Read back: the chord is still in voice 6 of the second staff, and nothing else moved
    MasterScore* reread = ScoreRW::readScore(u"eightvoices-moved.mscx", true);
    ASSERT_TRUE(reread);
    EngravingItem* rereadChord = reread->tick2segment(tick, true, SegmentType::ChordRest)->element(movedTrack);
    ASSERT_TRUE(rereadChord && rereadChord->isChord());
    EXPECT_EQ(toChord(rereadChord)->upNote()->pitch(), pitch);

    EXPECT_TRUE(ScoreRW::saveScore(reread, u"eightvoices-reread.mscx"));
    EXPECT_EQ(fileText(u"eightvoices-reread.mscx"), saved);

    // Copying from a score with voices beyond four marks the clipboard data, too
    score->select(toChord(moved)->measure(), SelectType::RANGE, 1);
    const String mimeData = String::fromUtf8(score->selection().mimeData());
    EXPECT_TRUE(mimeData.contains(String(u"version=\"%1\"").arg(String::fromAscii(Constants::MSC_VERSION_EIGHT_VOICES_STR))));

    // Without voices beyond four the score is saved in the standard format again, as before the move
    EditData ed;
    score->undoStack()->undo(&ed);
    EXPECT_TRUE(ScoreRW::saveScore(score, u"eightvoices-undone.mscx"));
    const String undone = fileText(u"eightvoices-undone.mscx");
    EXPECT_TRUE(undone.contains(versionTag(Constants::MSC_VERSION_STR)));
    EXPECT_EQ(undone, fileText(u"eightvoices-original.mscx"));

    delete reread;
    delete score;
}
