from django.core.serializers.python import Serializer

class LazyAccountEncoder(Serializer):
    def get_dump_object(self, obj) :
        dump_object = {}
        dump_object.update({'id': obj.id})
        dump_object.update({'email': obj.email})
        dump_object.update({'username': obj.username})
        dump_object.update({'profile_image': obj.profile_image.url})
        return dump_object
       