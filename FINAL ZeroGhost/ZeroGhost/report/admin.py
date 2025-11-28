# report/admin.py - Enhanced version with improved Facebook posting

from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Report
import requests
from django.conf import settings
import os

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'region_display', 
        'status_badge', 
        'approved_badge', 
        'photo_preview', 
        'created_at',
        'facebook_post_status'
    ]
    
    list_filter = ['region', 'status', 'approved', 'created_at']
    search_fields = ['region', 'description', 'latitude', 'longitude', 'id']
    readonly_fields = ['created_at', 'photo_preview_large', 'map_preview', 'id']
    date_hierarchy = 'created_at'
    
    actions = [
        'approve_reports', 
        'disapprove_reports',
        'mark_complete',
        'mark_incomplete',
        'post_to_facebook'
    ]
    
    fieldsets = (
        ('Report ID', {
            'fields': ('id',)
        }),
        ('Location Information', {
            'fields': ('region', 'latitude', 'longitude', 'map_preview'),
            'description': 'Geographic location details of the reported project'
        }),
        ('Report Details', {
            'fields': ('status', 'description', 'photo', 'photo_preview_large'),
            'description': 'Project status and supporting documentation'
        }),
        ('Administration', {
            'fields': ('approved', 'created_at'),
            'description': 'Administrative controls and metadata'
        }),
    )
    
    list_per_page = 25
    save_on_top = True
    
    # Display Methods
    def region_display(self, obj):
        return obj.get_region_display()
    region_display.short_description = 'Region'
    region_display.admin_order_field = 'region'
    
    def status_badge(self, obj):
        if obj.status == 'complete':
            color = '#28a745'
            icon = '✓'
            text = 'COMPLETE'
        else:
            color = '#dc3545'
            icon = '✗'
            text = 'Incomplete'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; '
            'border-radius: 4px; font-weight: bold; display: inline-block;">'
            '{} {}</span>',
            color, icon, text
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def approved_badge(self, obj):
        if obj.approved:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 5px 12px; border-radius: 4px; font-weight: bold;">'
                '✓ Approved</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #ffc107; color: #000; '
                'padding: 5px 12px; border-radius: 4px; font-weight: bold;">'
                'Pending</span>'
            )
    approved_badge.short_description = 'Approval Status'
    approved_badge.admin_order_field = 'approved'
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; '
                'object-fit: cover; border-radius: 5px; border: 2px solid #ddd;" />',
                obj.photo.url
            )
        return format_html(
            '<span style="color: #999; font-style: italic;">No Image</span>'
        )
    photo_preview.short_description = 'Preview'
    
    def photo_preview_large(self, obj):
        if obj.photo:
            return format_html(
                '<div style="text-align: center;">'
                '<img src="{}" style="max-width: 600px; max-height: 600px; '
                'border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />'
                '<p style="margin-top: 10px;"><a href="{}" target="_blank" '
                'style="color: #007bff;">Open full size image</a></p>'
                '</div>',
                obj.photo.url,
                obj.photo.url
            )
        return format_html(
            '<p style="color: #999; font-style: italic;">No image uploaded</p>'
        )
    photo_preview_large.short_description = 'Photo'
    
    def map_preview(self, obj):
        if obj.latitude and obj.longitude:
            return format_html(
                '''
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                    <iframe
                        width="100%"
                        height="450"
                        style="border:0; border-radius: 8px; margin-bottom: 15px;"
                        loading="lazy"
                        allowfullscreen
                        src="https://www.google.com/maps?q={},{}&z=15&output=embed">
                    </iframe>
                    <div style="background: white; padding: 12px; border-radius: 6px; margin-top: 10px;">
                        <p style="margin: 5px 0;"><strong>📍 Coordinates:</strong></p>
                        <p style="margin: 5px 0; font-family: monospace;">
                            Latitude: {}<br>
                            Longitude: {}
                        </p>
                        <a href="https://www.google.com/maps?q={},{}" 
                           target="_blank" 
                           style="display: inline-block; margin-top: 10px; padding: 8px 16px; 
                                  background: #007bff; color: white; text-decoration: none; 
                                  border-radius: 4px; font-weight: bold;">
                            🗺️ Open in Google Maps
                        </a>
                    </div>
                </div>
                ''',
                obj.latitude, obj.longitude,
                obj.latitude, obj.longitude,
                obj.latitude, obj.longitude
            )
        return format_html(
            '<p style="color: #999; font-style: italic;">No location data available</p>'
        )
    map_preview.short_description = 'Map Location'
    
    def facebook_post_status(self, obj):
        """Show if report is ready to post to Facebook"""
        if not obj.approved:
            return format_html(
                '<span style="color: #999;">Not approved</span>'
            )
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">✓ Ready</span>'
        )
    facebook_post_status.short_description = 'Facebook Status'
    
    # Admin Actions
    def approve_reports(self, request, queryset):
        updated = queryset.update(approved=True)
        self.message_user(
            request,
            f'✓ Successfully approved {updated} report(s).',
            messages.SUCCESS
        )
    approve_reports.short_description = "✓ Approve selected reports"
    
    def disapprove_reports(self, request, queryset):
        updated = queryset.update(approved=False)
        self.message_user(
            request,
            f'⏳ Marked {updated} report(s) as pending approval.',
            messages.WARNING
        )
    disapprove_reports.short_description = "Disapprove selected reports"
    
    def mark_complete(self, request, queryset):
        updated = queryset.update(status='complete')
        self.message_user(
            request,
            f'✓ Marked {updated} report(s) as complete.',
            messages.SUCCESS
        )
    mark_complete.short_description = "✓ Mark as Complete"
    
    def mark_incomplete(self, request, queryset):
        updated = queryset.update(status='incomplete')
        self.message_user(
            request,
            f'✗ Marked {updated} report(s) as incomplete.',
            messages.WARNING
        )
    mark_incomplete.short_description = "X Mark as Incomplete"
    
    # Facebook Integration
    def post_to_facebook(self, request, queryset):
        """
        Post approved reports to Facebook Page
        """
        # Check if Facebook credentials are configured
        facebook_access_token = getattr(settings, 'FACEBOOK_PAGE_ACCESS_TOKEN', None)
        facebook_page_id = getattr(settings, 'FACEBOOK_PAGE_ID', None)
        
        if not facebook_access_token or not facebook_page_id:
            self.message_user(
                request,
                'Facebook API credentials not configured. Please add FACEBOOK_PAGE_ACCESS_TOKEN '
                'and FACEBOOK_PAGE_ID to settings.py. See documentation for setup instructions.',
                messages.ERROR
            )
            return
        
        posted_count = 0
        failed_count = 0
        not_approved_count = 0
        
        for report in queryset:
            # Check if report is approved
            if not report.approved:
                not_approved_count += 1
                continue
            
            try:
                # Prepare the post content
                message = self.format_facebook_message(report)
                
                # Post to Facebook
                success = self.post_report_to_facebook(
                    facebook_page_id,
                    facebook_access_token,
                    message,
                    report
                )
                
                if success:
                    posted_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                self.message_user(
                    request,
                    f'Error posting report #{report.id}: {str(e)}',
                    messages.ERROR
                )
        
        # Show summary messages
        if posted_count > 0:
            self.message_user(
                request,
                f'Successfully posted {posted_count} report(s) to Facebook!',
                messages.SUCCESS
            )
        if not_approved_count > 0:
            self.message_user(
                request,
                f'Skipped {not_approved_count} unapproved report(s). Only approved reports can be posted.',
                messages.WARNING
            )
        if failed_count > 0:
            self.message_user(
                request,
                f'Failed to post {failed_count} report(s). Check your Facebook credentials and permissions.',
                messages.ERROR
            )
    
    post_to_facebook.short_description = "Post to Facebook Page"
    
    def format_facebook_message(self, report):
        """Format the report data into a Facebook post message"""
        status_emoji = "✓" if report.status == "complete" else "!"
        
        # Create description text
        description_text = report.description if report.description else 'No additional details provided.'
        
        message = f"""🏗️ ZeroGhost Infrastructure Report

{status_emoji} Status: {report.get_status_display()}
📍 Region: {report.get_region_display()}
📌 Location: {report.latitude}, {report.longitude}

{description_text}

🗺️ View on map: https://www.google.com/maps?q={report.latitude},{report.longitude}

#ZeroGhost #Infrastructure #PublicWorks #{report.get_region_display().replace(' ', '')}
""".strip()
        
        return message
    
    def post_report_to_facebook(self, page_id, access_token, message, report):
        """
        Post to Facebook Page using Graph API
        Returns True if successful, False otherwise
        """
        try:
            if report.photo and os.path.exists(report.photo.path):
                # Post with photo
                return self.post_with_photo(page_id, access_token, message, report)
            else:
                # Post text only
                return self.post_text_only(page_id, access_token, message)
                
        except Exception as e:
            print(f"Exception posting to Facebook: {e}")
            return False
    
    def post_with_photo(self, page_id, access_token, message, report):
        """Post with photo to Facebook"""
        try:
            url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
            
            with open(report.photo.path, 'rb') as photo_file:
                files = {'source': photo_file}
                data = {
                    'message': message,
                    'access_token': access_token
                }
                
                response = requests.post(url, data=data, files=files, timeout=30)
            
            # Check response
            if response.status_code == 200:
                response_data = response.json()
                print(f"✓ Successfully posted to Facebook. Post ID: {response_data.get('id')}")
                return True
            else:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                print(f"X Facebook API Error: {error_message}")
                print(f"Full response: {response.text}")
                return False
                
        except FileNotFoundError:
            print(f"X Photo file not found: {report.photo.path}")
            # Try posting without photo as fallback
            return self.post_text_only(page_id, access_token, message)
        except Exception as e:
            print(f"X Error posting with photo: {e}")
            return False
    
    def post_text_only(self, page_id, access_token, message):
        """Post text-only update to Facebook"""
        try:
            url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
            data = {
                'message': message,
                'access_token': access_token
            }
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"✓ Successfully posted text to Facebook. Post ID: {response_data.get('id')}")
                return True
            else:
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                print(f"X Facebook API Error: {error_message}")
                return False
                
        except Exception as e:
            print(f"X Error posting text: {e}")
            return False