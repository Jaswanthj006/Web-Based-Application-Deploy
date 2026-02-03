from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate
from django.http import FileResponse, Http404
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
import tempfile

from .models import EquipmentDataset, AuthToken
from .serializers import EquipmentDatasetSerializer, EquipmentDatasetDetailSerializer
from .services import parse_csv, dataframe_to_records


class AllowAnyMixin:
    permission_classes = [AllowAny]


class LoginView(AllowAnyMixin, APIView):
    """Basic auth: POST { username, password } -> returns token."""
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        token, _ = AuthToken.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.id, 'username': user.username})


class RegisterView(AllowAnyMixin, APIView):
    """Register: POST { username, password } -> create user and return token."""
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)
        if len(password) < 8:
            return Response({'error': 'Password must be at least 8 characters'}, status=status.HTTP_400_BAD_REQUEST)
        from django.contrib.auth.models import User
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=username, password=password)
        token = AuthToken.objects.create(user=user)
        return Response({'token': token.key, 'user_id': user.id, 'username': user.username}, status=status.HTTP_201_CREATED)


class UploadCSVView(APIView):
    """Upload CSV. Requires authentication. Keeps last 5 datasets."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file = request.FILES.get('file')
        if not file or not file.name.lower().endswith('.csv'):
            return Response({'error': 'CSV file required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
                for chunk in file.chunks():
                    tmp.write(chunk)
                tmp.flush()
                df, summary = parse_csv(tmp.name)
            os.unlink(tmp.name)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        name = request.data.get('name') or file.name
        dataset = EquipmentDataset.objects.create(
            name=name,
            file=file,
            uploaded_by=request.user,
            total_count=summary['total_count'],
            summary_json=summary,
        )
        # Keep only last 5
        for old in EquipmentDataset.objects.order_by('-uploaded_at')[5:]:
            if old.file:
                try:
                    old.file.delete()
                except Exception:
                    pass
            old.delete()

        return Response({
            'id': dataset.id,
            'name': dataset.name,
            'uploaded_at': dataset.uploaded_at,
            'total_count': dataset.total_count,
            'summary': dataset.summary_json,
        }, status=status.HTTP_201_CREATED)


class HistoryListView(AllowAnyMixin, APIView):
    """List last 5 uploaded datasets (summary only)."""
    def get(self, request):
        qs = EquipmentDataset.objects.order_by('-uploaded_at')[:5]
        serializer = EquipmentDatasetSerializer(qs, many=True)
        return Response(serializer.data)


class SummaryView(AllowAnyMixin, APIView):
    """Get summary for a dataset by ID."""
    def get(self, request, pk):
        try:
            dataset = EquipmentDataset.objects.get(pk=pk)
        except EquipmentDataset.DoesNotExist:
            raise Http404
        return Response({
            'id': dataset.id,
            'name': dataset.name,
            'total_count': dataset.total_count,
            'summary': dataset.summary_json,
        })


class DataTableView(AllowAnyMixin, APIView):
    """Get full table data for a dataset (from stored CSV)."""
    def get(self, request, pk):
        try:
            dataset = EquipmentDataset.objects.get(pk=pk)
        except EquipmentDataset.DoesNotExist:
            raise Http404
        if not dataset.file:
            return Response({'data': []})
        try:
            df, _ = parse_csv(dataset.file.path)
            records = dataframe_to_records(df)
            return Response({'data': records})
        except Exception as e:
            return Response({'error': str(e), 'data': []}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportPDFView(APIView):
    """Generate PDF report for a dataset. Requires authentication (Token or query param)."""
    permission_classes = []  # auth checked manually to allow ?token= for download links
    authentication_classes = []  # we'll authenticate manually

    def get(self, request, pk):
        token_key = request.GET.get('token') or request.headers.get('Authorization', '').replace('Token ', '')
        if token_key:
            try:
                token = AuthToken.objects.get(key=token_key)
                request.user = token.user
            except AuthToken.DoesNotExist:
                pass
        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            dataset = EquipmentDataset.objects.get(pk=pk)
        except EquipmentDataset.DoesNotExist:
            raise Http404
        try:
            df, _ = parse_csv(dataset.file.path) if dataset.file else (None, dataset.summary_json)
        except Exception:
            df = None
        summary = dataset.summary_json or {}

        fd, path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        doc = SimpleDocTemplate(path, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(name='Title', parent=styles['Heading1'], fontSize=16)
        story = []
        story.append(Paragraph('Chemical Equipment Parameter Report', title_style))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f'Dataset: {dataset.name}', styles['Normal']))
        story.append(Paragraph(f'Generated: {timezone.now().strftime("%Y-%m-%d %H:%M")}', styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph('Summary', styles['Heading2']))
        story.append(Paragraph(f"Total equipment count: {summary.get('total_count', 0)}", styles['Normal']))
        av = summary.get('averages', {})
        for k, v in (av or {}).items():
            if v is not None:
                story.append(Paragraph(f"Average {k}: {v}", styles['Normal']))
        type_dist = summary.get('type_distribution', {})
        if type_dist:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph('Equipment type distribution:', styles['Normal']))
            type_data = [['Type', 'Count']] + [[k, str(v)] for k, v in type_dist.items()]
            t = Table(type_data)
            t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12), ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black)]))
            story.append(t)
        if df is not None and len(df) > 0:
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph('Data sample (first 20 rows)', styles['Heading2']))
            sample = df.head(20)
            cols = list(sample.columns)
            table_data = [cols] + sample.fillna('').astype(str).values.tolist()
            t2 = Table(table_data, repeatRows=1)
            t2.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),                 ('GRID', (0, 0), (-1, -1), 0.25, colors.black)]))
            story.append(t2)
        doc.build(story)
        try:
            return FileResponse(open(path, 'rb'), as_attachment=True, filename=f'report_{dataset.id}.pdf')
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass
