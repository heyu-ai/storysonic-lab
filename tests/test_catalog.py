import unittest

from storysonic.catalog import Show, parse_feed, select_episodes, validate_url


SHOW = Show('detective-pig', '豬探長', 'ifkids', '如果兒童劇團', 'https://example.com/feed')


def item(guid='g1', title='故事', date='Tue, 01 Sep 2026 00:00:00 GMT', url='https://example.com/story.mp3'):
    return f'<item><guid>{guid}</guid><title>{title}</title><pubDate>{date}</pubDate><enclosure url="{url}" type="audio/mpeg" length="0"/></item>'


def feed(*items):
    return ('<rss><channel><title>節目</title>' + ''.join(items) + '</channel></rss>').encode()


class CatalogTests(unittest.TestCase):
    def test_newest_first_filter_limit_and_guid_deduplication(self):
        episodes = parse_feed(feed(item(), item('g2', '故事2', 'Thu, 03 Sep 2026 00:00:00 GMT'), item('g1')), SHOW)
        self.assertEqual([e['guid'] for e in select_episodes(episodes, '故事', 1)], ['g2'])
        self.assertEqual(len(episodes), 2)

    def test_stable_identity_does_not_depend_on_title(self):
        first = parse_feed(feed(item(title='old')), SHOW)[0]
        second = parse_feed(feed(item(title='new')), SHOW)[0]
        self.assertEqual(first['episode_key'], second['episode_key'])
        self.assertEqual(len(first['episode_key']), 24)

    def test_missing_date_sorts_last_and_missing_guid_uses_enclosure(self):
        episodes = parse_feed(feed(item('', date=''), item('dated')), SHOW)
        self.assertEqual(episodes[-1]['guid'], 'https://example.com/story.mp3')

    def test_no_enclosure_and_non_audio_are_not_download_candidates(self):
        self.assertEqual(parse_feed(feed('<item><title>ad</title></item>'), SHOW), [])
        self.assertEqual(parse_feed(feed('<item><enclosure url="https://example.com/a.pdf" type="application/pdf"/></item>'), SHOW), [])

    def test_untrusted_xml_is_rejected(self):
        for data in [b'<!DOCTYPE x [<!ENTITY e "test">]><rss/>', b'<html/>', b'<rss>']:
            with self.subTest(data=data), self.assertRaises(ValueError):
                parse_feed(data, SHOW)

    def test_invalid_ids_urls_and_limits_are_rejected(self):
        with self.assertRaises(ValueError):
            Show('../escape', 'x', 'a', 'a', 'https://example.com/feed')
        for url in ['file:///etc/passwd', 'https://user:pass@example.com/a', 'ftp://example.com/a', '']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_url(url)
        for limit in [0, -1]:
            with self.assertRaises(ValueError):
                select_episodes([], '', limit)
