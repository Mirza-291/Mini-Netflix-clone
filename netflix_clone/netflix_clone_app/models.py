# models.py

# from djongo import models

# class User(models.Model):
#     email = models.EmailField()
#     password = models.CharField(max_length=255)
#     watchlist = models.JSONField(default=list, blank=True)
#     genre = models.JSONField(default=list, blank=True)

#     class Meta:
#         managed = False   # ⬅️ Very important: tell Django not to manage (no migrations)
#         db_table = "users"  # ⬅️ Use your manual collection
