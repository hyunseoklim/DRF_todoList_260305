from django.db import models


class CollectedReview(models.Model):

    doc_id = models.CharField(max_length=255, primary_key=True)  # ← 여기만 있어야 함

    title = models.CharField(max_length=255)

    review = models.TextField()

    collected_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "stg_movie_reviews"
        managed = False

    def __str__(self):
        return self.title
