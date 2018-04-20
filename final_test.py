from final import *
import unittest

class TestDataAccess(unittest.TestCase):
    def test_scraping(self):
        c_list = retrieve_cities()
        self.assertEqual(len(c_list), 15)
        self.assertEqual(c_list[7].lat, '32.8153')
        self.assertEqual(c_list[7].lng, '-117.1350')

    def test_eat_street_api(self):
        resp = get_restaurants('40.6635', '-73.9387')
        self.assertIs(type(resp), dict)
        r_list = resp['restaurants']
        self.assertEqual(len(r_list), 19)
        resp = get_restaurant_menu('8489410df54f7260f15b4f2e73e761809d6e38bec0a5b05c')
        self.assertIs(type(resp), list)

class TestDataStorage(unittest.TestCase):
    def test_restaurants_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        statement = '''
            SELECT COUNT(*)
                FROM Restaurants
            '''
        cur.execute(statement)
        size = cur.fetchone()[0]
        statement = '''
            SELECT RestaurantName, City, State
                FROM Restaurants
                WHERE APIKey = "8489410df54f7260144247b91fbcb2f39f14d8d7561637ff"
            '''
        cur.execute(statement)
        q = cur.fetchone()
        self.assertEqual(size, 101)
        self.assertEqual(q[0], 'Cafe Chili')
        self.assertEqual(q[1], 'Brooklyn')
        self.assertEqual(q[2], 'NY')
        conn.close()

    def test_padthaiitems_table(self):
        conn = sqlite3.connect(DBNAME)
        cur = conn.cursor()
        statement = '''
            SELECT COUNT(*)
                FROM PadThaiItems
            '''
        cur.execute(statement)
        size = cur.fetchone()[0]
        statement = '''
            SELECT ItemName, BasePrice
                FROM PadThaiItems
                WHERE RestaurantAPIKey = "8489410df54f7260144247b91fbcb2f39f14d8d7561637ff"
            '''
        cur.execute(statement)
        q = cur.fetchall()
        self.assertEqual(size, 203)
        self.assertEqual(q[0][0], '54. Pad Thai')
        self.assertEqual(q[0][1], 11.0)
        self.assertEqual(q[1][0], '51. Naked Pad Thai')
        self.assertEqual(q[1][1], 17.0)
        conn.close()

class TestProcessingProcedures(unittest.TestCase):
    def test_geoplot(self):
        self.assertEqual(len(get_restaurants_for_state('NY')), 18)
        self.assertEqual(len(get_restaurants_for_state('IL')), 24)
        self.assertEqual(len(get_restaurants_for_state('__')), 101)

    def test_bar_chart(self):
        r = retrieve_avg_state_prices()
        self.assertEqual(len(r), 10)
        self.assertEqual(r[0][0], 'AZ')
        self.assertEqual(r[0][1], 11.376923076923076)

    def test_histogram(self):
        r = retrieve_all_base_prices()
        self.assertEqual(len(r), 203)
        self.assertEqual(r[3][0], 12.0)
        self.assertEqual(r[5][0], 15.0)

    def test_scatterplot(self):
        self.assertEqual(len(retrieve_all_avg_prices('NY')), 17)
        self.assertEqual(len(retrieve_all_avg_prices('IL')), 24)
        self.assertEqual(len(retrieve_all_avg_prices('__')), 99)

if __name__ == '__main__':
    unittest.main()
