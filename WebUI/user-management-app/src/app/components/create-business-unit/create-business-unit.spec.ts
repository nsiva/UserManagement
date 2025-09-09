import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CreateBusinessUnit } from './create-business-unit';

describe('CreateBusinessUnit', () => {
  let component: CreateBusinessUnit;
  let fixture: ComponentFixture<CreateBusinessUnit>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [CreateBusinessUnit]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CreateBusinessUnit);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
