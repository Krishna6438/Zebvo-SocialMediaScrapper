import unittest
from datetime import datetime
import nlp_engine

class TestNLPEngine(unittest.TestCase):

    def test_gibberish_filter(self):
        # Clearly gibberish/spam posts
        self.assertTrue(nlp_engine.is_gibberish("asdfghjklqwertyuiop"))
        self.assertTrue(nlp_engine.is_gibberish("aaaaa"))
        self.assertTrue(nlp_engine.is_gibberish("!!! $$$ %%% zxczxczxczxc"))
        
        # Short string is gibberish/not useful
        self.assertTrue(nlp_engine.is_gibberish("pass"))
        
        # Valid posts should NOT be gibberish
        self.assertFalse(nlp_engine.is_gibberish(
            "Jalandhar PSK is completely booked out. Tried booking a Tatkal slot but it failed."
        ))
        self.assertFalse(nlp_engine.is_gibberish(
            "My experience of passport renewal was amazing! Staff was helpful and fast."
        ))

    def test_categorization(self):
        # Appointment keyword
        txt_apt = "I need to book an appointment slot at Jalandhar PSK for my visa interview."
        self.assertEqual(nlp_engine.classify_category(txt_apt), "Appointments")

        # Tatkal keyword
        txt_tat = "How much are the Tatkal fees for urgent passport application dispatch?"
        self.assertEqual(nlp_engine.classify_category(txt_tat), "Tatkal")

        # Visa keyword
        txt_visa = "Is a student visa stamp required for traveling to Schengen countries?"
        self.assertEqual(nlp_engine.classify_category(txt_visa), "Visa")

        # Scams keyword
        txt_scam = "Beware of fake websites charging extra money for passport booking, agent scam warning!"
        self.assertEqual(nlp_engine.classify_category(txt_scam), "Scams/Fraud")

    def test_sentiment_analysis(self):
        # Positive sentiment
        self.assertEqual(nlp_engine.analyze_sentiment("This service is excellent and super helpful! Highly recommended."), "Positive")
        
        # Negative sentiment
        self.assertEqual(nlp_engine.analyze_sentiment("Terrible experience, very slow process and rude staff. So frustrating."), "Negative")
        
        # Neutral sentiment
        self.assertEqual(nlp_engine.analyze_sentiment("The passport office is located on the main road in Jalandhar."), "Neutral")

    def test_generate_summary(self):
        long_text = (
            "The Ministry of External Affairs has officially launched a new DigiLocker integration for passport applications today. "
            "Under this new system, applicants can share their paperless documents securely from their digital locker account. "
            "This cuts the verification times by almost fifty percent and completely reduces the need to carry physical documents. "
            "It will also speed up police verification processes as the records are verified at source. "
            "The regional passport officer in Jalandhar said this is a revolutionary step for citizens who want to renew quickly."
        )
        summary = nlp_engine.generate_summary(long_text)
        word_count = len(summary.split())
        
        # Check that it extracted the key sentences and kept the length reasonable (~30-35 words limit)
        self.assertTrue(word_count <= 40, f"Summary word count is {word_count}, expected <= 40")
        self.assertTrue(word_count >= 10, f"Summary word count is {word_count}, expected >= 10")
        self.assertIn("DigiLocker", summary)

    def test_clustering(self):
        posts = [
            {"id": 1, "content": "MEA announces new digital verification using DigiLocker for passport applicants."},
            {"id": 2, "content": "MEA announces new digital verification using DigiLocker for passport applicants."}, # Exact duplicate
            {"id": 3, "content": "Jalandhar PSK has no slots. I tried booking a slot at Jalandhar PSK and there are no appointments available."},
            {"id": 4, "content": "Jalandhar PSK has no slots. Jalandhar PSK has no slots available for passport appointments."}, # Semantically similar
            {"id": 5, "content": "Applied for a travel visa to Europe last week and hope it arrives in time."}
        ]
        
        clustered = nlp_engine.cluster_posts(posts, similarity_threshold=0.5)
        
        # Post 1 and 2 should be in the same cluster
        self.assertIsNotNone(clustered[0]["cluster_id"])
        self.assertEqual(clustered[0]["cluster_id"], clustered[1]["cluster_id"])
        
        # Post 3 and 4 should be in the same cluster (different from post 1/2)
        self.assertIsNotNone(clustered[2]["cluster_id"])
        self.assertEqual(clustered[2]["cluster_id"], clustered[3]["cluster_id"])
        self.assertNotEqual(clustered[0]["cluster_id"], clustered[2]["cluster_id"])
        
        # Post 5 is unique, should have cluster_id None (noise)
        self.assertIsNone(clustered[4]["cluster_id"])

if __name__ == "__main__":
    unittest.main()
