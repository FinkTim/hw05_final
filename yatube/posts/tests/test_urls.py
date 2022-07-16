from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.core.cache import cache

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user
        )
        Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.index_url = '/'
        cls.group_list_url = '/group/test-slug/'
        cls.profile_url = f'/profile/{cls.user.username}/'
        cls.post_detail = f'/posts/{cls.post.pk}/'
        cls.post_create = '/create/'
        cls.post_edit = f'/posts/{cls.post.pk}/edit/'
        cls.post_comment = f'/posts/{cls.post.pk}/comment/'

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(PostURLTests.user)

    def test_urls_uses_correct_template_author(self):
        """URL-адрес использует соответствующий шаблон для автора поста."""
        templates_url_names = {
            self.index_url: 'posts/index.html',
            self.group_list_url: 'posts/group_list.html',
            self.profile_url: 'posts/profile.html',
            self.post_detail: 'posts/post_detail.html',
            self.post_create: 'posts/create_post.html',
            self.post_edit: 'posts/create_post.html'
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_authorized(self):
        """URL-адрес использует соответствующий шаблон для
        авторизированного пользователя."""
        templates_url_names = {
            self.index_url: 'posts/index.html',
            self.group_list_url: 'posts/group_list.html',
            self.profile_url: 'posts/profile.html',
            self.post_detail: 'posts/post_detail.html',
            self.post_create: 'posts/create_post.html',
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_homepage(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get(self.index_url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_page(self):
        """Страница group/slug доступна любому пользователю."""
        response = self.guest_client.get(self.group_list_url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_page(self):
        """Страница profile/username доступна любому пользователю."""
        response = self.guest_client.get(self.profile_url)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_detail_page(self):
        """Страница posts/post_id доступна любому пользователю."""
        response = self.guest_client.get(self.post_detail)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_page(self):
        """Страница create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get(self.post_create)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_page(self):
        """Страница post/pk/edit доступна автору поста."""

        response = self.authorized_author.get(self.post_edit)

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_page_redirect_anonymous_on_login(self):
        """Страница по адресу create/ перенаправит
        анонимного пользователя на страницу логина.
        """
        response = self.guest_client.get(self.post_create, follow=True)

        self.assertRedirects(
            response, '/auth/login/?next=%2Fcreate%2F'
        )

    def test_post_edit_page_redirect_anonymous_on_login(self):
        """Страница по адресу posts/edit перенаправит
        анонимного пользователя на страницу логина.
        """
        response = self.guest_client.get(self.post_edit, follow=True)

        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{PostURLTests.post.pk}/edit/'
        )

    def test_post_edit_page_redirect_authorized_on_post_detial(self):
        """Страница по адресу posts/edit перенаправит
        авторизированного пользователя, не автора на страницу post_detail.
        """
        response = self.authorized_client.get(self.post_edit)

        self.assertRedirects(response, self.post_detail)

    def test_unexisting_page(self):
        """Страница с несуществующим адресом возвращает 404"""
        response = self.guest_client.get('/unexisting_page/')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_add_comment_page_redirect_anonymous_on_login(self):
        """Страница по адресу posts/<int:pk>/comment/ перенаправит
        анонимного пользователя на страницу логина.
        """
        response = self.guest_client.get(self.post_comment, follow=True)

        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.pk}/comment/'
        )
