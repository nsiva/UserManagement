import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';
import { FunctionalRolesHierarchyService, FunctionalRoleHierarchyItem, FunctionalRoleHierarchyResponse } from '../../services/functional-roles-hierarchy';
import { OrganizationService, Organization } from '../../services/organization';
import { HeaderComponent } from '../../shared/components/header/header.component';
import { HeaderConfig } from '../../shared/interfaces/header-config.interface';
import { AlertComponent, AlertType } from '../../shared/components/alert/alert.component';
import { APP_NAME } from '../../shared/constants/app-constants';

@Component({
  selector: 'app-functional-roles-hierarchy-view',
  standalone: true,
  imports: [CommonModule, FormsModule, HeaderComponent, AlertComponent],
  templateUrl: './functional-roles-hierarchy-view.html',
  styleUrl: './functional-roles-hierarchy-view.scss'
})
export class FunctionalRolesHierarchyViewComponent implements OnInit {
  headerConfig: HeaderConfig = {
    title: APP_NAME,
    subtitle: 'Functional Roles Hierarchy',
    showUserMenu: true
  };

  // Data properties
  hierarchyData: FunctionalRoleHierarchyItem[] = [];
  filteredHierarchy: FunctionalRoleHierarchyItem[] = [];
  organizations: Organization[] = [];
  isLoading = false;
  
  // Filter properties
  selectedOrganizationId: string = '';
  selectedCategory: string = '';
  showOnlyEnabled = false;
  searchTerm = '';

  // Summary properties
  totalOrganizations = 0;
  totalBusinessUnits = 0;
  totalRoles = 0;

  // Alert properties
  alertMessage: string | null = null;
  alertType: AlertType = 'info';

  // Available filter options
  availableCategories: string[] = [];

  constructor(
    private functionalRolesService: FunctionalRolesHierarchyService,
    private organizationService: OrganizationService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadOrganizations();
    this.loadHierarchyData();
  }

  private loadOrganizations(): void {
    this.organizationService.getOrganizations().subscribe({
      next: (organizations) => {
        this.organizations = organizations;
      },
      error: (error) => {
        console.error('Error loading organizations:', error);
        this.showError('Failed to load organizations');
      }
    });
  }

  private loadHierarchyData(organizationId?: string): void {
    this.isLoading = true;
    
    this.functionalRolesService.getFunctionalRoleHierarchy(organizationId).subscribe({
      next: (response: FunctionalRoleHierarchyResponse) => {
        this.hierarchyData = response.hierarchy;
        this.totalOrganizations = response.total_organizations;
        this.totalBusinessUnits = response.total_business_units;
        this.totalRoles = response.total_roles;
        
        this.updateAvailableCategories();
        this.applyFilters();
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading hierarchy data:', error);
        this.showError('Failed to load functional roles hierarchy');
        this.isLoading = false;
      }
    });
  }

  private updateAvailableCategories(): void {
    const categories = new Set(this.hierarchyData.map(item => item.functional_role_category));
    this.availableCategories = Array.from(categories).sort();
  }

  applyFilters(): void {
    this.filteredHierarchy = this.hierarchyData.filter(item => {
      // Organization filter
      if (this.selectedOrganizationId && item.organization_id !== this.selectedOrganizationId) {
        return false;
      }

      // Category filter
      if (this.selectedCategory && item.functional_role_category !== this.selectedCategory) {
        return false;
      }

      // Show only enabled filter
      if (this.showOnlyEnabled && !item.enabled_at_org) {
        return false;
      }

      // Search term filter
      if (this.searchTerm) {
        const term = this.searchTerm.toLowerCase();
        return (
          item.organization_name.toLowerCase().includes(term) ||
          (item.business_unit_name && item.business_unit_name.toLowerCase().includes(term)) ||
          item.functional_role_name.toLowerCase().includes(term) ||
          item.functional_role_label.toLowerCase().includes(term)
        );
      }

      return true;
    });
  }

  onOrganizationFilterChange(): void {
    if (this.selectedOrganizationId) {
      this.loadHierarchyData(this.selectedOrganizationId);
    } else {
      this.loadHierarchyData();
    }
  }

  onFilterChange(): void {
    this.applyFilters();
  }

  clearFilters(): void {
    this.selectedOrganizationId = '';
    this.selectedCategory = '';
    this.showOnlyEnabled = false;
    this.searchTerm = '';
    this.loadHierarchyData();
  }

  refreshData(): void {
    this.loadHierarchyData(this.selectedOrganizationId || undefined);
  }

  // Group hierarchy items by organization for display
  getGroupedHierarchy(): { [orgId: string]: { organization: string; items: FunctionalRoleHierarchyItem[] } } {
    const grouped: { [orgId: string]: { organization: string; items: FunctionalRoleHierarchyItem[] } } = {};
    
    this.filteredHierarchy.forEach(item => {
      if (!grouped[item.organization_id]) {
        grouped[item.organization_id] = {
          organization: item.organization_name,
          items: []
        };
      }
      grouped[item.organization_id].items.push(item);
    });

    return grouped;
  }

  // Navigation methods
  navigateToOrganization(organizationId: string): void {
    this.router.navigate(['/admin/organizations', organizationId]);
  }

  navigateToBusinessUnit(businessUnitId: string): void {
    this.router.navigate(['/admin/business-units', businessUnitId]);
  }

  navigateToProfile(): void {
    this.router.navigate(['/profile']);
  }

  navigateToAdmin(): void {
    this.router.navigate(['/admin']);
  }

  logout(): void {
    this.authService.logout();
  }

  // Alert methods
  showError(message: string): void {
    this.alertMessage = message;
    this.alertType = 'error';
  }

  showSuccess(message: string): void {
    this.alertMessage = message;
    this.alertType = 'success';
  }

  showInfo(message: string): void {
    this.alertMessage = message;
    this.alertType = 'info';
  }

  onAlertDismissed(): void {
    this.alertMessage = null;
  }
}