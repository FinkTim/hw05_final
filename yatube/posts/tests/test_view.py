import shutil
import tempfile

from django import forms
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.cache import cache

from posts.models import Group, Post, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

        cls.index_url = 'posts:index'
        cls.group_list_url = 'posts:group_list'
        cls.profile_url = 'posts:profile'
        cls.post_detail = 'posts:post_detail'
        cls.post_create = 'posts:post_create'
        cls.post_edit = 'posts:post_edit'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client.force_login(PostPagesTest.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse(self.index_url): 'posts/index.html',
            reverse(
                self.group_list_url,
                kwargs={
                    'slug': 'test-slug'}): 'posts/group_list.html',
            reverse(
                self.profile_url,
                kwargs={
                    'username': self.user.username}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={
                    'pk': self.post.pk}): 'posts/post_detail.html',
            reverse(self.post_create): 'posts/create_post.html',
            reverse(
                self.post_edit,
                kwargs={
                    'pk': self.post.pk}): 'posts/create_post.html'}

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                self.authorized_client.force_login(PostPagesTest.user)
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_edit_post_show_correct_context(self):
        """Шаблон edit_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'pk': self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(self.index_url))

        first_object = response.context['page_obj'][0]

        self.assertEqual(first_object, self.post)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))

        first_object = response.context['page_obj'][0]
        second_object = response.context['group']
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_image_0 = first_object.image
        group_title_0 = second_object.title
        group_description_0 = second_object.description

        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_author_0, PostPagesTest.user)
        self.assertEqual(post_image_0, self.post.image)
        self.assertEqual(group_title_0, 'Тестовый заголовок')
        self.assertEqual(group_description_0, 'Тестовое описание')

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                self.profile_url, kwargs={
                    'username': PostPagesTest.user}))

        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_image_0 = first_object.image

        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_author_0, PostPagesTest.user)
        self.assertEqual(post_image_0, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(self.post_detail, kwargs={'pk': self.post.pk}))

        self.assertEqual(response.context.get('post').text, 'Тестовый текст')
        self.assertEqual(
            response.context.get('post').author,
            PostPagesTest.user)
        self.assertEqual(
            response.context.get('post').group,
            PostPagesTest.group)
        self.assertEqual(
            response.context.get('post').image,
            PostPagesTest.post.image)

    def test_post_create_group_append_exist_on_index(self):
        """Пост с группой отображается на главной странице"""
        Post.objects.create(
            text='Новый пост',
            author=PostPagesTest.user,
            group=PostPagesTest.group,
        )
        pages = (
            reverse(self.index_url), reverse(
                self.group_list_url, kwargs={
                    'slug': PostPagesTest.group.slug}), reverse(
                self.profile_url, kwargs={
                    'username': PostPagesTest.user}),)

        for reverse_page in pages:
            with self.subTest(reverse_page=reverse_page):
                response = self.authorized_client.get(reverse_page)
                count_posts = len(response.context['page_obj'])
                self.assertEqual(count_posts, 2)

    def test_post_is_in_the_right_group(self):
        """Пост не попал в другую группу"""
        Group.objects.create(
            title='Другая группа',
            description='Другая группа для теста',
            slug='new-group-slug'
        )
        response = self.authorized_client.get(
            reverse(
                self.group_list_url, kwargs={
                    'slug': 'new-group-slug'}))
        obj = response.context['page_obj']
        self.assertTrue(len(obj) == 0)

    def test_cache(self):
        """Данные страницы index кешируются"""
        new_post = Post.objects.create(
            text='Новый пост c кешем',
            author=PostPagesTest.user,
            group=PostPagesTest.group,
        )

        response_before = self.guest_client.get(reverse(self.index_url))
        content = response_before.content
        new_post.delete()

        response_after = self.guest_client.get(reverse(self.index_url))
        self.assertEqual(content, response_after.content)
        cache.clear()

        response_clear = self.guest_client.get(reverse(self.index_url))
        self.assertNotEqual(content, response_clear)


class PaginatorViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.posts = 15
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug',
        )
        for _ in range(cls.posts):
            cls.post = Post.objects.create(
                text='Тестовый текст',
                author=cls.user,
                group=cls.group
            )
        cls.index_url = 'posts:index'
        cls.group_list_url = 'posts:group_list'
        cls.profile_url = 'posts:profile'

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_first_page_contains_ten_records(self):
        """На первую страницу index выводятся 10 постов"""
        response = self.client.get(reverse(self.index_url))

        self.assertEqual(
            len(response.context['page_obj']), settings.POSTS_PER_PAGE)

    def test_index_second_page_contains_five_records(self):
        """На вторую страницу index выводятся 5 постов"""
        response = self.client.get(reverse(self.index_url) + '?page=2')

        self.assertEqual(
            len(response.context['page_obj']),
            self.posts - settings.POSTS_PER_PAGE)

    def test_group_first_page_contains_ten_records(self):
        """На первую страницу group выводятся 10 постов"""
        response = self.client.get(
            reverse(
                self.group_list_url,
                kwargs={
                    'slug': 'test-slug'}))

        self.assertEqual(
            len(response.context['page_obj']), settings.POSTS_PER_PAGE)

    def test_group_second_page_contains_five_records(self):
        """На вторую страницу group выводятся 5 постов"""
        response = self.client.get(
            reverse(
                self.group_list_url, kwargs={
                    'slug': 'test-slug'}) + '?page=2')

        self.assertEqual(
            len(response.context['page_obj']),
            self.posts - settings.POSTS_PER_PAGE)

    def test_profile_first_page_contains_ten_records(self):
        """На первую страницу profile выводятся 10 постов"""
        response = self.client.get(
            reverse(
                self.profile_url, kwargs={
                    'username': PaginatorViewTest.user}))

        self.assertEqual(
            len(response.context['page_obj']), settings.POSTS_PER_PAGE)

    def test_profile_second_page_contains_five_records(self):
        """На вторую страницу profile выводятся 5 постов"""
        response = self.client.get(
            reverse(
                self.profile_url, kwargs={
                    'username': PaginatorViewTest.user}) + '?page=2')

        self.assertEqual(
            len(response.context['page_obj']),
            self.posts - settings.POSTS_PER_PAGE)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Тестовый пользователь')
        cls.user_2 = User.objects.create_user(
            username='Тестовый пользователь 2')
        cls.follower = User.objects.create_user(username='Подписчик')
        cls.following = User.objects.create_user(username='Автор')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.following,
        )
        cls.follow = Follow.objects.create(
            user=cls.follower,
            author=cls.following
        )

    def setUp(self):
        cache.clear()
        self.client_follower = Client()
        self.client_following = Client()
        self.client_user = Client()
        self.clinet_user_2 = Client()
        self.client_follower.force_login(self.follower)
        self.client_following.force_login(self.following)
        self.client_user.force_login(self.user)
        self.clinet_user_2.force_login(self.user_2)

    def test_profile_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей
        """
        follow_count = Follow.objects.count()
        self.client_user.post(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_2.username}
        ))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_profile_unfollow(self):
        """Авторизованный пользователь может отписываться
        от других пользователей
        """
        follow_count = Follow.objects.count()
        self.client_follower.post(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.following.username}
        ))
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_new_post_appear_for_follower(self):
        """Новый пост появляется для подписчика на странцие follow"""
        response = self.client_follower.get(reverse('posts:follow_index'))
        page_obj = response.context['page_obj']

        self.assertTrue(len(page_obj) == 1)

    def test_new_post_doesnt_appear_for_unfollower(self):
        """Новый пост не появляется для других на странцие follow"""
        response = self.client_user.get(reverse('posts:follow_index'))
        page_obj = response.context['page_obj']

        self.assertTrue(len(page_obj) == 0)
