# EasyTest RBAC – Login details

After running **`python manage.py seed_dummy_data`**, you can use these accounts:

| Role         | Email                     | Password     |
|-------------|----------------------------|--------------|
| **Super Admin** | `superadmin@easytest.com`   | `EasyTest@123` |
| **School Admin** | `schooladmin@easytest.com` | `EasyTest@123` |
| **Teacher**     | `teacher@easytest.com`      | `EasyTest@123` |

- **Super Admin**: full access; can manage Schools, create School Admins and Teachers.
- **School Admin**: access limited to **Demo School**; can create Teachers for that school.
- **Teacher**: access limited to **Demo School** and only their own exams/participants.

Seed also creates **Demo School** and assigns the dummy participants and exams to it so School Admin and Teacher see data after login.

If you use **`python manage.py createsuperuser`** instead, that user gets **Super Admin** on first login (via auto-created profile).
