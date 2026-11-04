"""Opt-in read-only integration test: python -m unittest tests.test_neighborhood_summary.

Uses the configured PostgreSQL database, without starting the API or changing data.
"""
import asyncio
import math
import selectors
import statistics
import unittest
from datetime import date
from zoneinfo import ZoneInfo

import psycopg
from psycopg.rows import dict_row

from app.database.connection import conninfo
from app.services.neighborhoods import load_neighborhoods, select_unique_members
from app.services.neighborhood_summary import CATEGORIES, PROPERTY_SQL, CRIME_SQL, summarize_connection


class SummaryIntegrationTests(unittest.IsolatedAsyncioTestCase):
    loop_factory = staticmethod(lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))

    async def test_sql_edge_cases(self):
        async with await psycopg.AsyncConnection.connect(conninfo, row_factory=dict_row) as conn:
            await conn.execute("SET TRANSACTION READ ONLY")
            fixture = """(VALUES
                ('a', 100::bigint, 10::float8), ('b', 200, 20),
                ('c', 0, 'NaN'::float8), ('d', -1, 'Infinity'::float8),
                ('e', NULL, NULL), ('f', 0, -1), ('g', 0, 0)
            ) AS fixture(parcel_number, current_assessed_value, lot_sqft)"""
            query = PROPERTY_SQL.replace('public.real_estate_current_assessment', fixture)
            row = await (await conn.execute(query, {'ids': list('abcdefg') + ['a']})).fetchone()
            self.assertEqual(row['property_count'], 7)
            self.assertEqual(row['median_assessed_value'], 150)
            self.assertEqual(row['total_assessed_value'], 300)
            self.assertEqual(row['median_lot_sqft'], 15)
            self.assertEqual(row['lot_sqft_excluded_count'], 5)
            empty = await (await conn.execute(query, {'ids': []})).fetchone()
            self.assertEqual(empty['property_count'], 0)
            self.assertIsNone(empty['total_assessed_value'])
            self.assertIsNone(empty['median_assessed_value'])
            fixture = """(VALUES
                (1, '  BURGLARY  ', '2025-03-09 05:00:00+00'::timestamptz),
                (2, NULL, '2025-03-10 03:59:59+00'::timestamptz),
                (3, 'new offense', '2025-03-09 12:00:00+00'::timestamptz),
                (4, 'Burglary', '2025-03-10 04:00:00+00'::timestamptz),
                (5, 'Burglary', '2025-03-09 04:59:59+00'::timestamptz)
            ) AS fixture(record_id, offense, date_reported)"""
            query = CRIME_SQL.replace('public.crime', fixture)
            groups = await (await conn.execute(query, {
                'ids': [1, 2, 3, 4, 5], 'offenses': ['burglary'], 'categories': ['burglary'],
                'date_start': date(2025, 3, 9), 'date_end': date(2025, 3, 9),
            })).fetchall()
            self.assertEqual({g['category']: g['count'] for g in groups}, {'burglary': 1, 'other': 2})
            self.assertEqual(sum(g['missing_count'] for g in groups), 1)
            self.assertTrue(all(g['total_count'] == 3 for g in groups))

    async def test_three_neighborhoods(self):
        async with await psycopg.AsyncConnection.connect(conninfo, row_factory=dict_row) as conn:
            await conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
            await conn.execute("SET LOCAL statement_timeout = '20s'")
            properties = await (await conn.execute(
                "SELECT * FROM public.real_estate_current_assessment "
                "WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
            )).fetchall()
            crimes = await (await conn.execute(
                "SELECT * FROM public.crime WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
            )).fetchall()
            polygons = load_neighborhoods()
            for neighborhood_id, name in ((16, "Fry's Spring"), (6, "Greenbrier"), (10, "Belmont-Carlton")):
                parcels, _ = select_unique_members(properties, neighborhood_id, polygons)
                parcels = {p['parcel_number']: p for p in parcels}.values()
                values = [p['current_assessed_value'] for p in parcels if p['current_assessed_value'] > 0]
                lots = [p['lot_sqft'] for p in parcels if math.isfinite(p['lot_sqft']) and p['lot_sqft'] > 0]
                for start, end in ((None, None), (date(2025, 1, 1), date(2025, 12, 31)),
                                   (date(1900, 1, 1), date(1900, 1, 1))):
                    with self.subTest(neighborhood=name, start=start):
                        result = await summarize_connection(conn, neighborhood_id, start, end)
                        filtered = [c for c in crimes if start is None or
                                    start <= c['date_reported'].astimezone(ZoneInfo('America/New_York')).date() <= end]
                        accepted, ambiguous = select_unique_members(filtered, neighborhood_id, polygons)
                        counts = dict.fromkeys(CATEGORIES, 0)
                        for crime in accepted:
                            offense = (crime['offense'] or '').strip().lower()
                            category = next((key for key, names in CATEGORIES.items()
                                             if offense in [n.lower() for n in names]), 'other')
                            counts[category] += 1
                        self.assertEqual(result['property_count'], len(parcels))
                        self.assertEqual(result['median_assessed_value'], statistics.median(values) if values else None)
                        self.assertEqual(result['total_assessed_value'], sum(values) if values else None)
                        self.assertAlmostEqual(result['median_lot_sqft'], statistics.median(lots))
                        self.assertEqual(result['assessed_value_valid_count'], len(values))
                        self.assertEqual(result['lot_sqft_excluded_count'], len(parcels) - len(lots))
                        self.assertEqual(result['crime_count'], len(accepted))
                        self.assertEqual(result['crime_by_category'], counts)
                        self.assertEqual(result['crime_count'], sum(counts.values()))
                        self.assertEqual(result['ambiguous_crime_count'], ambiguous)
                        print(name, start or 'all dates', result['property_count'], result['crime_count'],
                              result['median_assessed_value'], result['median_lot_sqft'])
            for start, end in ((date(2025, 1, 1), None), (date(2025, 2, 1), date(2025, 1, 1))):
                with self.assertRaises(ValueError):
                    await summarize_connection(conn, 16, start, end)


if __name__ == '__main__':
    unittest.main()
