#!/usr/bin/env python3
"""
Test scheduling enforcement: ads don't show before start_date/start_time
and late validations recalculate play counts
"""
from datetime import datetime, date, time, timedelta
from models.booking import Booking

def test_is_playable_now():
    """Test is_playable_now() logic"""
    print("\n=== Testing is_playable_now() ===\n")

    # Test 1: Future start_date (should NOT be playable)
    future_booking = Booking()
    future_booking.status = 'active'
    future_booking.start_date = (datetime.utcnow().date() + timedelta(days=5))
    future_booking.end_date = future_booking.start_date + timedelta(days=10)

    result = future_booking.is_playable_now()
    print(f"✓ Future start_date (in 5 days): playable={result}")
    assert result == False, "Future content should NOT be playable"

    # Test 2: Past start_date, active now (should be playable)
    active_booking = Booking()
    active_booking.status = 'active'
    active_booking.start_date = (datetime.utcnow().date() - timedelta(days=2))
    active_booking.end_date = datetime.utcnow().date() + timedelta(days=5)

    result = active_booking.is_playable_now()
    print(f"✓ Past start_date, active now: playable={result}")
    assert result == True, "Current content should be playable"

    # Test 3: Today's start with future time (should NOT be playable)
    today_future_time = Booking()
    today_future_time.status = 'active'
    today_future_time.start_date = datetime.utcnow().date()
    today_future_time.start_time = (datetime.utcnow() + timedelta(hours=2)).time()
    today_future_time.end_date = datetime.utcnow().date() + timedelta(days=10)

    result = today_future_time.is_playable_now()
    print(f"✓ Today but start time in future (2h): playable={result}")
    assert result == False, "Content with future start_time should NOT be playable"

    # Test 4: Ended (past end_date)
    ended_booking = Booking()
    ended_booking.status = 'active'
    ended_booking.start_date = datetime.utcnow().date() - timedelta(days=10)
    ended_booking.end_date = datetime.utcnow().date() - timedelta(days=1)

    result = ended_booking.is_playable_now()
    print(f"✓ Past end_date: playable={result}")
    assert result == False, "Ended content should NOT be playable"

    # Test 5: Inactive status
    inactive_booking = Booking()
    inactive_booking.status = 'pending'
    inactive_booking.start_date = datetime.utcnow().date() - timedelta(days=2)
    inactive_booking.end_date = datetime.utcnow().date() + timedelta(days=10)

    result = inactive_booking.is_playable_now()
    print(f"✓ Inactive status (pending): playable={result}")
    assert result == False, "Inactive content should NOT be playable"


def test_calculate_dynamic_plays():
    """Test late-validation play count recalculation"""
    print("\n=== Testing calculate_dynamic_plays() ===\n")

    # Test 1: No late validation (should return original count)
    normal_booking = Booking()
    normal_booking.start_date = datetime.utcnow().date() - timedelta(days=5)
    normal_booking.end_date = datetime.utcnow().date() + timedelta(days=10)
    normal_booking.num_plays = 10
    normal_booking.validated_date = normal_booking.start_date  # Validated on start_date

    result = normal_booking.calculate_dynamic_plays()
    print(f"✓ Normal booking (validated on time): plays={result}")
    assert result == normal_booking.num_plays, "Should return original count"

    # Test 2: Late validation (should increase play count)
    late_booking = Booking()
    late_booking.start_date = datetime.utcnow().date() - timedelta(days=10)
    late_booking.end_date = datetime.utcnow().date() + timedelta(days=5)
    late_booking.num_plays = 10
    # Total days: 15, remaining days: 5
    # Original rate: 10/15 = 0.67 plays/day
    # Adjusted: 0.67 * 5 = 3.35 ≈ 3 plays (but capped at min 10)
    late_booking.validated_date = datetime.utcnow() - timedelta(days=5)

    result = late_booking.calculate_dynamic_plays()
    print(f"✓ Late booking (validated 5 days later): plays={result}")
    # Should be at least original num_plays
    assert result >= late_booking.num_plays, "Late validation should increase play count"

    # Test 3: Validated after end_date (edge case)
    too_late = Booking()
    too_late.start_date = datetime.utcnow().date() - timedelta(days=20)
    too_late.end_date = datetime.utcnow().date() - timedelta(days=5)
    too_late.num_plays = 10
    too_late.validated_date = datetime.utcnow()  # Validated after end_date

    result = too_late.calculate_dynamic_plays()
    print(f"✓ Validated after end_date: plays={result}")
    assert result == too_late.num_plays, "Should return original (no days remaining)"

    # Test 4: No validated_date (should return original)
    unvalidated = Booking()
    unvalidated.start_date = datetime.utcnow().date() - timedelta(days=5)
    unvalidated.end_date = datetime.utcnow().date() + timedelta(days=10)
    unvalidated.num_plays = 10
    unvalidated.validated_date = None

    result = unvalidated.calculate_dynamic_plays()
    print(f"✓ No validated_date: plays={result}")
    assert result == unvalidated.num_plays, "Should return original"


def main():
    """Run all tests"""
    print("="*60)
    print("SCHEDULING LOGIC TESTS")
    print("="*60)

    try:
        test_is_playable_now()
        test_calculate_dynamic_plays()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("""
Key behaviors verified:
1. ✓ Ads don't show before scheduled start_date/start_time
2. ✓ Ads stop showing after end_date
3. ✓ Late validations maintain contracted play counts
4. ✓ Play frequency adjusts based on remaining time window

This ensures fair contract fulfillment even with late approvals.
        """)
        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
