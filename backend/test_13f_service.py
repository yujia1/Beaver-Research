"""
Test script for 13F filing service.
Tests fetching, parsing, and processing 13F filings.
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from services.filing_13f_service import filing_13f_service
from models import Filing13F

def test_get_quarter_from_date():
    """Test quarter calculation"""
    print("Testing quarter calculation...")
    test_dates = [
        (datetime(2024, 1, 15), "2024-Q1"),
        (datetime(2024, 4, 15), "2024-Q2"),
        (datetime(2024, 7, 15), "2024-Q3"),
        (datetime(2024, 10, 15), "2024-Q4"),
    ]
    
    all_passed = True
    for date, expected in test_dates:
        result = filing_13f_service.get_quarter_from_date(date)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {date.strftime('%Y-%m-%d')} -> {result} (expected {expected})")
        if result != expected:
            all_passed = False
    
    return all_passed

def test_get_all_13f_filings():
    """Test fetching 13F filings from EDGAR"""
    print("\nTesting 13F filing fetch from EDGAR...")
    try:
        # Test with recent date range (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"  Fetching filings from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
        filings = filing_13f_service.get_all_13f_filings(start_date, end_date)
        
        print(f"  ✓ Found {len(filings)} 13F filings")
        
        if filings:
            # Show first few
            print(f"  Sample filings:")
            for filing in filings[:3]:
                print(f"    - CIK: {filing['cik']}, Form: {filing['form_type']}, Date: {filing['filing_date'].strftime('%Y-%m-%d')}")
        
        return len(filings) > 0
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_process_single_filing():
    """Test processing a single 13F filing"""
    print("\nTesting single filing processing...")
    db = SessionLocal()
    try:
        # Get a recent filing
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        filings = filing_13f_service.get_all_13f_filings(start_date, end_date)
        
        if not filings:
            print("  ⚠ No filings found to test")
            return False
        
        # Try to process the first 13F-HR filing (not 13F-NT)
        test_filing = None
        for filing in filings:
            if filing['form_type'] == '13F-HR':
                test_filing = filing
                break
        
        if not test_filing:
            print("  ⚠ No 13F-HR filings found to test")
            return False
        
        print(f"  Processing filing: {test_filing['accession_number']} for CIK {test_filing['cik']}")
        
        result = filing_13f_service.process_filing(db, test_filing, force_reprocess=False)
        
        if result:
            print(f"  ✓ Successfully processed filing")
            
            # Check database
            db_filing = db.query(Filing13F).filter(
                Filing13F.accession_number == test_filing['accession_number']
            ).first()
            
            if db_filing:
                print(f"  ✓ Filing saved to database:")
                print(f"    - ID: {db_filing.id}")
                print(f"    - Quarter: {db_filing.quarter}")
                print(f"    - Holdings: {db_filing.holdings_count}")
                print(f"    - MinIO Path: {db_filing.minio_path}")
                return True
            else:
                print(f"  ✗ Filing not found in database")
                return False
        else:
            print(f"  ✗ Failed to process filing (may already be processed)")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_quarter_comparison():
    """Test quarter-over-quarter comparison"""
    print("\nTesting quarter comparison...")
    db = SessionLocal()
    try:
        # Find a CIK with filings in multiple quarters
        ciks = db.query(Filing13F.cik).distinct().all()
        
        if not ciks:
            print("  ⚠ No CIKs with processed filings found")
            return False
        
        # Find a CIK with multiple quarters
        test_cik = None
        for (cik,) in ciks:
            quarters = db.query(Filing13F.quarter).filter(
                Filing13F.cik == cik
            ).distinct().all()
            if len(quarters) >= 2:
                test_cik = cik
                break
        
        if not test_cik:
            print("  ⚠ No CIK with multiple quarters found")
            return False
        
        # Get quarters
        quarters = sorted([q[0] for q in db.query(Filing13F.quarter).filter(
            Filing13F.cik == test_cik
        ).distinct().all()])
        
        if len(quarters) < 2:
            print("  ⚠ Need at least 2 quarters for comparison")
            return False
        
        current_quarter = quarters[-1]
        prior_quarter = quarters[-2]
        
        print(f"  Comparing CIK {test_cik}:")
        print(f"    Current: {current_quarter}")
        print(f"    Prior: {prior_quarter}")
        
        result = filing_13f_service.compare_quarters(
            db, test_cik, current_quarter, prior_quarter, min_change_pct=5.0
        )
        
        if 'error' in result:
            print(f"  ✗ Error: {result['error']}")
            return False
        
        print(f"  ✓ Comparison completed:")
        print(f"    - New positions: {result['new_positions_count']}")
        print(f"    - Closed positions: {result['closed_positions_count']}")
        print(f"    - Size changes: {result['size_changes_count']}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_minio_connection():
    """Test MinIO connection"""
    print("\nTesting MinIO connection...")
    try:
        filing_13f_service._ensure_bucket_exists()
        client = filing_13f_service._get_minio_client()
        client.head_bucket(Bucket=filing_13f_service.minio_bucket)
        print(f"  ✓ MinIO connection successful (bucket: {filing_13f_service.minio_bucket})")
        return True
    except Exception as e:
        print(f"  ✗ MinIO connection failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("13F Filing Service Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Quarter calculation
    results.append(("Quarter Calculation", test_get_quarter_from_date()))
    
    # Test 2: MinIO connection
    results.append(("MinIO Connection", test_minio_connection()))
    
    # Test 3: Fetch filings
    results.append(("Fetch 13F Filings", test_get_all_13f_filings()))
    
    # Test 4: Process single filing
    results.append(("Process Single Filing", test_process_single_filing()))
    
    # Test 5: Quarter comparison (only if we have data)
    results.append(("Quarter Comparison", test_quarter_comparison()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  ✓ All tests passed!")
    else:
        print(f"\n  ⚠ {total - passed} test(s) failed")

if __name__ == "__main__":
    main()

